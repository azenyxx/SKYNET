import os,time,sys
from cognitive_parallel_contracts import *
from cognitive_parallel_operators import execute

def worker(receive,send,unused,task,fault='NORMAL'):
 # Only fixed code is reached. No provider, model, module path or function is supplied.
 try:
  sys.addaudithook(lambda e,a: (_ for _ in ()).throw(RuntimeError('NETWORK_FORBIDDEN')) if e.startswith('socket.') else None)
  for endpoint in unused:endpoint.close()
  send.send_bytes(b'READY')
  if not receive.poll(3) or receive.recv_bytes(16)!=b'GO':return
  if fault=='CRASH':os._exit(73)
  if fault=='DELAY':time.sleep(.25)
  result=WorkerResultV1(task.commitment,1,execute(task));send.send_bytes(canonical(result))
 finally:
  try:receive.close()
  finally:send.close()
