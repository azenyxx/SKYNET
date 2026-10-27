from fixtures import *

class Tests(Base):
 def test_chain(self):
  b,d=flight();j=snap(b).journal;verify_chain(j,4096);self.assertEqual(j[1].previous_record_hash,j[0].record_hash)
 def test_tamper_hash(self):
  b=ready();j=snap(b).journal;self.bad('JOURNAL_TAMPERED',lambda:verify_chain((replace(j[0],record_hash='a'*64),),4096))
 def test_tamper_payload(self):
  b=ready();j=snap(b).journal;self.bad('JOURNAL_TAMPERED',lambda:verify_chain((replace(j[0],command=FrozenJSON.make({})),),4096))
 def test_missing(self):
  b=ready();j=snap(b).journal;self.bad('JOURNAL_TAMPERED',lambda:verify_chain(j[1:],4096))
 def test_order(self):
  b=ready();j=snap(b).journal;self.bad('JOURNAL_TAMPERED',lambda:verify_chain(tuple(reversed(j)),4096))
 def test_limit(self):
  b=ready(journal_limit=1);self.bad('JOURNAL_FULL',lambda:b.inspect('admin',0));self.assertEqual(len(b._journal),1)
 def test_denial_audited(self):
  b=ready();self.bad('CAPABILITY_DENIED',lambda:b.subscribe('evil',Q,'other',0));self.assertEqual(b._journal[-1].authorization_decision,'DENY')
 def test_deterministic(self):
  a=ready();b=ready();self.assertEqual(snap(a).journal,snap(b).journal)
