"""Explicit operational executor; legacy observation Recovery API remains unchanged."""
from skynet.coordination import Coordinator,RecoveryRequest,require
from .restore import RestoreAdapter,RestoreRequest
class RecoveryExecutor:
 def __init__(self,coordinator,restorer):
  require(type(coordinator)is Coordinator and type(restorer)is RestoreAdapter,'CONTRACT');self.coordinator=coordinator;self.restorer=restorer
 def execute(self,action,request,tick=0):
  if action=='RESTORE_CHECKPOINT':
   require(type(request)is RestoreRequest,'REQUEST');return self.restorer.execute(request)
  require(action in ('RETRY','REQUEUE','RELEASE_LEASE') and type(request)is RecoveryRequest and request.recovery_policy==action,'ACTION');return self.coordinator.execute(request,tick)
