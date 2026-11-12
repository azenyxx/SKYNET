"""Read-only, locally observed predecessor snapshots; no independent truth claims."""
from skynet_sys.canonical import digest,FrozenJSON
from .core import Telemetry,need
class Observer:
 def __init__(self,workers,verification):self.workers=workers;self.verification=verification
 def event(self,kind,eid,component,tick,subject='task'):
  w=self.workers;source=None
  if kind=='WORKER_FAILED':
   need(subject in w.core.workers and w.core.workers[subject].lifecycle_state=='UNAVAILABLE','NOT_OBSERVED');source=w.core.state_digest()
  elif kind=='LEASE_EXPIRED':
   need(subject in w.core.leases and w.core.leases[subject].lease_state=='EXPIRED','NOT_OBSERVED');source=w.core.state_digest()
  elif kind=='TASK_STARVATION':
   cp=w.scheduler.checkpoint(w.actor);cp.verify();rows={r.value()[0]:r.value() for r in cp.tasks};need(subject in rows and rows[subject][11]=='READY' and tick-rows[subject][4]>5,'NOT_OBSERVED');source=cp.commitment
  elif kind=='BACKPRESSURE':
   s=w.bus.inspect(w.actor);need(dict(s.metrics)['queue_depth']>=w.bus.config.queue_limit,'NOT_OBSERVED');source=s.state_digest
  elif kind in ('VERIFICATION_REJECTED','VERIFICATION_CONFLICT'):
   need(subject in self.verification.rounds,'NOT_OBSERVED');r=self.verification.rounds[subject]
   need(bool(r['conflicts']) if kind=='VERIFICATION_CONFLICT' else r['decision'] is not None and r['decision'].final_verdict in ('FAIL','REJECTED'),'NOT_OBSERVED');source=self.verification.state_digest()
  else:need(False,'OBSERVATION_UNSUPPORTED')
  return Telemetry(eid,component,kind,'ERROR',tick,subject,FrozenJSON.make({'observed':True,'source_commitment':source}))
 def checkpoint(self,actor,key):return self.workers.memory.read(actor,'agent',key)
