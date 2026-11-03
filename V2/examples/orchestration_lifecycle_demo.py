"""Public illustrative lifecycle model; NOT SKYNET production source code."""
from dataclasses import dataclass
from enum import Enum


class State(str, Enum):
    CREATED = "CREATED"
    BOUND = "BOUND"
    RUNNING = "RUNNING"
    SEALED = "SEALED"
    REFUSED = "REFUSED"
    HALTED = "HALTED"


TERMINAL = frozenset({State.SEALED, State.REFUSED, State.HALTED})


@dataclass
class BoundedLifecycle:
    """Tiny fail-closed demonstration; no planning or authorization engine."""

    max_steps: int = 3
    state: State = State.CREATED
    steps: int = 0

    def preflight(self, *, test_profile: bool, snapshot_current: bool) -> State:
        if self.state is not State.CREATED:
            raise ValueError("preflight is allowed only once")
        if self.max_steps <= 0 or not test_profile or not snapshot_current:
            self.state = State.REFUSED
        else:
            self.state = State.BOUND
        return self.state

    def start(self) -> State:
        if self.state is not State.BOUND:
            raise ValueError("cannot start from current state")
        self.state = State.RUNNING
        return self.state

    def step(self) -> State:
        if self.state is not State.RUNNING:
            raise ValueError("not running")
        if self.steps >= self.max_steps:
            self.state = State.HALTED
        else:
            self.steps += 1
        return self.state

    def finish(self, *, evidence_persisted: bool) -> State:
        if self.state is not State.RUNNING:
            raise ValueError("cannot finish from current state")
        self.state = State.SEALED if evidence_persisted else State.HALTED
        return self.state

    def stop(self) -> State:
        if self.state not in TERMINAL:
            self.state = State.HALTED
        return self.state
