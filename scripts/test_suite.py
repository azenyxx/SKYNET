"""One suite process; counts come directly from unittest's result object."""
import sys,json,unittest
from pathlib import Path
folder,output=sys.argv[1:];suite=unittest.defaultTestLoader.discover(folder)
result=unittest.TextTestRunner(verbosity=2).run(suite)
Path(output).write_text(json.dumps({'collected':result.testsRun,'PASS':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped)-len(result.expectedFailures)-len(result.unexpectedSuccesses),'FAIL':len(result.failures),'ERROR':len(result.errors),'SKIP':len(result.skipped),'expected_failures':len(result.expectedFailures),'unexpected_successes':len(result.unexpectedSuccesses)},indent=2))
sys.exit(not result.wasSuccessful() or bool(result.skipped or result.expectedFailures or result.unexpectedSuccesses))
