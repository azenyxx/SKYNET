"""Answer-free subprocess with bounded file-read and no external effect audit policy."""
import sys,json,os
from pathlib import Path
from .evidence import need
source=Path(__file__).resolve().parents[1]
runtime=Path(sys.base_prefix).resolve()
forbidden={'benchmark.py','scoring.py','runner.py'}
def guard(event,args):
 if event=='open':
  path,mode,flags=args
  if isinstance(path,int):return
  resolved=Path(path).resolve()
  if (mode and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise PermissionError('VALIDATION_WRITE_DENIED')
  if not (resolved.is_relative_to(source) or resolved.is_relative_to(runtime)):raise PermissionError('VALIDATION_READ_DENIED')
  if resolved.is_relative_to(source/'skynet_validation') and (resolved.name in forbidden or any(resolved.name.startswith(x[:-3]+'.') for x in forbidden)):raise PermissionError('ANSWER_KEY_DENIED')
 if event.startswith(('socket.','subprocess.','ctypes.')) or event in ('os.system','os.posix_spawn','os.fork','os.exec','os.remove','os.rename','os.mkdir','os.rmdir'):raise PermissionError('EXTERNAL_EFFECT_DENIED')
sys.addaudithook(guard)
from .adapter import execute
raw=sys.stdin.buffer.read(262145);need(len(raw)<=262144,'SIZE');task=json.loads(raw);output=execute(task)
need('skynet_validation.benchmark' not in sys.modules and 'skynet_validation.scoring' not in sys.modules,'ANSWER_MODULE_LOADED')
print(json.dumps(output,sort_keys=True,allow_nan=False))
