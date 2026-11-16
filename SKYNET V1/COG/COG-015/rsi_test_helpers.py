import unittest,tempfile
from pathlib import Path
from dataclasses import replace
from cognitive_rsi_contracts import *
from cognitive_rsi_baseline import freeze
from cognitive_rsi_evaluation import observe,evaluate
from cognitive_rsi_proposals import propose
from cognitive_rsi_verification import challenge
from cognitive_rsi_policy import decide
from cognitive_rsi_adapter import simulate_cycle
from cognitive_rsi_registry import ImprovementRegistry
H='0'*64
def session(scenario='RESOURCE',sid='s',action='CONTINUE'):return simulate_cycle('n',sid,scenario,action)
