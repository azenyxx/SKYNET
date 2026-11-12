from copy import deepcopy
from dataclasses import replace
from skynet_sys.canonical import digest,ident,FrozenJSON,canonical
from skynet_sys.errors import ContractError
from .contracts import *
from .authorization import Authority
from .journal import record,verify_chain,JournalRecord
METRICS=('published_total','rejected_total','delivered_total','acknowledged_total','retried_total','dead_lettered_total','expired_total','duplicate_total')
class Bus:
    """Single-threaded trusted-host API. Not a sandbox, remote endpoint or scheduler."""
    def __init__(self,config,topics,authority):
        need(type(config) is Config);config.__post_init__();need(type(authority) is Authority);authority.__post_init__()
        need(type(topics) is tuple and 0<len(topics)<=32)
        for t in topics:need(type(t) is Topic);t.__post_init__()
        need(len({t.name for t in topics})==len(topics))
        self.config=config;self.topics=tuple(sorted(topics,key=lambda t:t.name));self.authority=authority
        self._initial=digest('sys002-config',(config,tuple((t.name,t.message_types,t.capability) for t in self.topics),authority.commitment))
        self._s=dict(clock=0,closed=False,sequence=0,subscriptions={},messages={},deliveries={},dlq={},metrics={k:0 for k in METRICS},pressure='NORMAL')
        self._journal=[]
    def _topic(self,name):
        topic_name(name);t=next((t for t in self.topics if t.name==name),None);need(t is not None,'UNKNOWN_TOPIC');return t
    def _scope(self,s,op,a):
        if op in ('publish','subscribe'):return self._topic(a['topic'])
        if op in ('unsubscribe','poll'):
            ident(a['subscription_id']);need(a['subscription_id'] in s['subscriptions'],'NOT_FOUND');return self._topic(s['subscriptions'][a['subscription_id']].topic)
        if op in ('ack','nack'):
            ident(a['delivery_id']);need(a['delivery_id'] in s['deliveries'],'NOT_FOUND');return self._topic(s['deliveries'][a['delivery_id']].topic)
        return None
    def _state_digest(self,s):
        roots=tuple((k,collection_digest('sys002-'+k,tuple((key,value) for key,value in sorted(s[k].items())))) for k in ('subscriptions','messages','deliveries','dlq'))
        return digest('sys002-state',(self._initial,s['clock'],s['closed'],s['sequence'],s['pressure'],tuple(sorted(s['metrics'].items())),roots))
    def _depth(self,s):return sum(d.delivery_status not in TERMINAL for d in s['deliveries'].values())
    def _move(self,s,d,status,**kw):
        transition(d.delivery_status,status);v=replace(d,delivery_status=status,**kw);s['deliveries'][d.delivery_id]=v;return v
    def _retry(self,s,d,tick,reason):
        if d.attempt_number>=self.config.retry.max_attempts:
            need(len(s['dlq'])<self.config.dead_letter_limit,'DLQ_FULL')
            v=self._move(s,d,'DEAD_LETTERED');s['dlq'][d.delivery_id]=DeadLetter(d.message_id,d.delivery_id,d.topic,d.consumer_id,reason,d.attempt_number,len(self._journal));s['metrics']['dead_lettered_total']+=1;return v
        s['metrics']['retried_total']+=1
        return self._move(s,d,'RETRY_PENDING',available_at=tick+self.config.retry.retry_delay_ticks,visibility_deadline=0)
    def _advance(self,s,tick):
        need(tick>=s['clock'],'CLOCK_ROLLBACK');now=self.config.at(tick)
        for key in sorted(s['deliveries']):
            d=s['deliveries'][key]
            if d.delivery_status in TERMINAL:continue
            msg=s['messages'][d.message_id][1]
            if now>=msg.expires_at:self._move(s,d,'EXPIRED');s['metrics']['expired_total']+=1;continue
            if d.delivery_status=='IN_FLIGHT' and tick>=d.visibility_deadline:d=self._retry(s,d,tick,'VISIBILITY_TIMEOUT')
            if d.delivery_status=='RETRY_PENDING' and tick>=d.available_at:self._move(s,d,'AVAILABLE')
        s['clock']=tick
    def _apply(self,s,op,actor,a,tick):
        need(not s['closed'] or op in ('inspect','close'),'CLOSED')
        # ACK replay is checked before timeout progression. It never reactivates a delivery.
        if op=='ack':
            d=s['deliveries'][a['delivery_id']];need(d.consumer_id==actor,'WRONG_CONSUMER');nat(a['attempt_number'],1,10)
            if d.delivery_status=='ACKNOWLEDGED':
                need(d.attempt_number==a['attempt_number'],'STALE_ATTEMPT');return d,'DUPLICATE_ACK'
        self._advance(s,tick)
        if op=='subscribe':
            ident(a['subscription_id']);need(a['subscription_id'] not in s['subscriptions'],'DUPLICATE_MESSAGE')
            need(len(s['subscriptions'])<self.config.subscription_limit,'SUBSCRIPTION_LIMIT')
            sub=Subscription(a['subscription_id'],actor,a['topic']);s['subscriptions'][sub.subscription_id]=sub;return sub,'OK'
        if op=='unsubscribe':
            sub=s['subscriptions'][a['subscription_id']];need(sub.consumer_id==actor,'WRONG_CONSUMER')
            need(not any(d.subscription_id==sub.subscription_id and d.delivery_status not in TERMINAL for d in s['deliveries'].values()),'BUSY')
            sub=replace(sub,active=False);s['subscriptions'][sub.subscription_id]=sub;return sub,'OK'
        if op=='publish':
            msg=decode_message(a['message']);msg.validate_at(self.config.at(tick));t=self._topic(a['topic'])
            need(msg.producer_id==actor and msg.recipient_id==self.config.bus_id,'CAPABILITY_DENIED');need(msg.message_type in t.message_types,'INVALID_SCHEMA')
            need(len(canonical(msg))<=self.config.message_limit,'MESSAGE_TOO_LARGE')
            if msg.message_id in s['messages']:
                oldtopic,old=s['messages'][msg.message_id]
                need(old.commitment==msg.commitment and oldtopic==t.name,'IDENTITY_CONFLICT');raise BusError('DUPLICATE_MESSAGE')
            need(len(s['messages'])<self.config.history_limit,'HISTORY_FULL')
            subs=sorted((x for x in s['subscriptions'].values() if x.topic==t.name and x.active),key=lambda x:x.subscription_id)
            need(bool(subs),'NO_SUBSCRIBERS')
            for sub in subs:self.authority.authorize(sub.consumer_id,'subscribe',t.name,t.capability)
            need(self._depth(s)+len(subs)<=self.config.queue_limit,'QUEUE_FULL')
            need(len(s['deliveries'])+len(subs)<=8192,'HISTORY_FULL')
            s['messages'][msg.message_id]=(t.name,msg);s['sequence']+=1;out=[]
            for sub in subs:
                did='d:'+digest('sys002-delivery',(msg.message_id,sub.subscription_id))
                d=Delivery(did,msg.message_id,msg.commitment,sub.subscription_id,sub.consumer_id,t.name,0,s['sequence'],0,tick,0,tick,'PENDING')
                s['deliveries'][did]=d;out.append(self._move(s,d,'AVAILABLE'))
            s['metrics']['published_total']+=1;return tuple(out),'OK'
        if op=='poll':
            sub=s['subscriptions'][a['subscription_id']];need(sub.consumer_id==actor,'WRONG_CONSUMER');need(sub.active,'NOT_FOUND')
            queue=sorted((d for d in s['deliveries'].values() if d.subscription_id==sub.subscription_id and d.delivery_status not in TERMINAL),key=lambda d:(d.sequence_number,d.delivery_id))
            if not queue or queue[0].delivery_status!='AVAILABLE':return None,'OK'
            d=queue[0];v=self._move(s,d,'IN_FLIGHT',attempt_number=d.attempt_number+1,visibility_deadline=tick+self.config.retry.visibility_timeout_ticks)
            s['metrics']['delivered_total']+=1;return v,'OK'
        if op in ('ack','nack'):
            d=s['deliveries'][a['delivery_id']];need(d.consumer_id==actor,'WRONG_CONSUMER');nat(a['attempt_number'],1,10)
            need(d.delivery_status=='IN_FLIGHT','INVALID_TRANSITION');need(d.attempt_number==a['attempt_number'],'STALE_ATTEMPT')
            if op=='ack':s['metrics']['acknowledged_total']+=1;return self._move(s,d,'ACKNOWLEDGED'),'OK'
            need(type(a['reason']) is str and a['reason'] in ('REJECTED','TRANSIENT','INVALID_RESULT'))
            return self._retry(s,d,tick,a['reason']),'OK'
        if op=='close':s['closed']=True;return True,'OK'
        return None,'OK'
    def _execute(self,op,actor,tick,args):
        need(type(op) is str and op in OPS);ident(actor);nat(tick)
        shapes={'publish':{'topic','message'},'subscribe':{'topic','subscription_id'},'unsubscribe':{'subscription_id'},'poll':{'subscription_id'},'ack':{'delivery_id','attempt_number'},'nack':{'delivery_id','attempt_number','reason'},'advance':set(),'inspect':set(),'close':set(),'replay':{'count','head'}}
        need(type(args) is dict and set(args)==shapes[op])
        if op=='replay':
            nat(args['count'],0,self.config.replay_limit)
            from skynet_sys.canonical import digest_text
            digest_text(args['head'])
        cmd=FrozenJSON.make(dict(op=op,actor=actor,tick=tick,args=args))
        need(len(self._journal)<self.config.journal_limit,'JOURNAL_FULL')
        # Replay authorization is audit-only: no clock, queues, counters or CLOSED mutation.
        if op=='replay':
            error=None;code='OK';decision='ALLOW'
            try:self.authority.authorize(actor,'replay','admin')
            except (BusError,ContractError) as ex:
                error=BusError(ex.code);code=ex.code;decision='DENY'
            j=record(len(self._journal),cmd,self._journal[-1].record_hash if self._journal else '0'*64,self._state_digest(self._s),code,decision)
            self._journal.append(j)
            if error:raise error
            return None
        before=self._s;s=deepcopy(before);allowed=False;error=None;result=None;code='OK'
        try:
            t=self._scope(s,op,args);self.authority.authorize(actor,op,t.name if t else 'admin',t.capability if t else 'system.observe');allowed=True
            need(tick>=s['clock'],'CLOCK_ROLLBACK')
            result,code=self._apply(s,op,actor,args,tick)
            if code=='DUPLICATE_ACK':return result
            s['pressure']=('REJECTING' if before['pressure']=='REJECTING' else 'SATURATED') if self._depth(s)>=self.config.queue_limit else 'NORMAL'
        except (BusError,ContractError) as ex:
            code=ex.code;error=BusError(code);s=deepcopy(before);s['metrics']['rejected_total']+=1
            if code in ('DUPLICATE_MESSAGE','IDENTITY_CONFLICT'):s['metrics']['duplicate_total']+=1
            if code=='QUEUE_FULL':s['pressure']='REJECTING'
        j=record(len(self._journal),cmd,self._journal[-1].record_hash if self._journal else '0'*64,self._state_digest(s),code,'ALLOW' if allowed else 'DENY')
        self._s=s;self._journal.append(j)
        if error:raise error
        return result
    def publish(self,actor,topic,message,tick):return self._execute('publish',actor,tick,dict(topic=topic,message=wire(message)))
    def subscribe(self,actor,topic,subscription_id,tick):return self._execute('subscribe',actor,tick,dict(topic=topic,subscription_id=subscription_id))
    def unsubscribe(self,actor,subscription_id,tick):return self._execute('unsubscribe',actor,tick,dict(subscription_id=subscription_id))
    def poll(self,actor,subscription_id,tick):return self._execute('poll',actor,tick,dict(subscription_id=subscription_id))
    def ack(self,actor,delivery_id,attempt_number,tick):return self._execute('ack',actor,tick,dict(delivery_id=delivery_id,attempt_number=attempt_number))
    def nack(self,actor,delivery_id,attempt_number,reason,tick):return self._execute('nack',actor,tick,dict(delivery_id=delivery_id,attempt_number=attempt_number,reason=reason))
    def advance(self,actor,tick):self._execute('advance',actor,tick,{});return tick
    def close(self,actor,tick):return self._execute('close',actor,tick,{})
    def inspect(self,actor,tick):
        self._execute('inspect',actor,tick,{})
        metrics=dict(self._s['metrics'],queue_depth=self._depth(self._s),in_flight_count=sum(d.delivery_status=='IN_FLIGHT' for d in self._s['deliveries'].values()),journal_length=len(self._journal))
        return Inspection(self._state_digest(self._s),tuple(sorted(metrics.items())),self._s['pressure'],tuple(self._s['deliveries'][k] for k in sorted(self._s['deliveries'])),tuple(self._s['dlq'][k] for k in sorted(self._s['dlq'])),tuple(self._journal))
    def replay(self,actor,records):
        need(type(records) is tuple and len(records)<=self.config.replay_limit,'REPLAY_LIMIT')
        head=records[-1].record_hash if records and type(records[-1]) is JournalRecord else '0'*64
        self._execute('replay',actor,self._s['clock'],dict(count=len(records),head=head))
        verify_chain(records,self.config.replay_limit)
        out=Bus(self.config,self.topics,self.authority)
        for original in records:
            c=original.command.value()
            need(type(c) is dict and set(c)=={'op','actor','tick','args'},'JOURNAL_TAMPERED')
            try:out._execute(c['op'],c['actor'],c['tick'],c['args'])
            except BusError:pass
            need(len(out._journal)==original.journal_sequence+1 and out._journal[-1]==original,'REPLAY_DIVERGENCE')
        return out
