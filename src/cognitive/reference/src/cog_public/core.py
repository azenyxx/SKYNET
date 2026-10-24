"""Small, self-contained cognitive workflow illustration.

This module is an independently written educational example. It does not
reproduce private SKYNET contracts, adapters, verification, or orchestration.
"""
from dataclasses import dataclass
import hashlib
import json
from typing import Literal

Operation = Literal['normalize', 'count_words', 'reverse']


@dataclass(frozen=True)
class Task:
    task_id: str
    operation: Operation
    text: str

    def __post_init__(self) -> None:
        if not self.task_id or len(self.task_id) > 64:
            raise ValueError('invalid task_id')
        if self.operation not in ('normalize', 'count_words', 'reverse'):
            raise ValueError('operation is not allowlisted')
        if not isinstance(self.text, str) or len(self.text) > 4096:
            raise ValueError('invalid text')


@dataclass(frozen=True)
class Result:
    task_id: str
    status: str
    value: str
    input_digest: str
    output_digest: str
    note: str = 'DEMO_ONLY_NOT_VERIFIED'


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def run(task: Task) -> Result:
    """Run one pure local operation. No tools, network, memory, or privileges."""
    if not isinstance(task, Task):
        raise TypeError('Task required')
    if task.operation == 'normalize':
        output = ' '.join(task.text.split())
    elif task.operation == 'count_words':
        output = str(len(task.text.split()))
    elif task.operation == 'reverse':
        output = task.text[::-1]
    else:
        raise ValueError('operation is not allowlisted')
    return Result(task.task_id, 'COMPLETED', output,
                  digest({'operation': task.operation, 'text': task.text}),
                  digest({'output': output}))
