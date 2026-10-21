"""Public educational example; not the private SKYNET implementation."""

def ready_tasks(tasks: dict[str, tuple[str, ...]], done: set[str]) -> list[str]:
    if any(dep not in tasks for deps in tasks.values() for dep in deps):
        raise ValueError("unknown dependency")
    return sorted(task for task, deps in tasks.items() if task not in done and all(d in done for d in deps))
