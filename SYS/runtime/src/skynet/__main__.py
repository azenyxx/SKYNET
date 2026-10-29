import json
from .system import workload
print(json.dumps(workload(),indent=2))
