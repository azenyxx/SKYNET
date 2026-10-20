"""Run a safe local demonstration: python -m cog_public.demo"""
from .core import Task, run


def main() -> None:
    for operation in ('normalize', 'count_words', 'reverse'):
        result = run(Task('example-' + operation, operation, '  hello   world  '))
        print(f'{operation}: {result.value} [{result.note}]')


if __name__ == '__main__':
    main()
