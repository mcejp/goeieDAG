from dataclasses import dataclass
from pathlib import Path
from typing import List, Union, Sequence


CmdArgument = Union[Path, str]


@dataclass
class _Task:
    command: Sequence[CmdArgument]
    inputs: Sequence[Path]
    outputs: Sequence[Path]


# Deliberately not named BuildError, because it represents a non-specific failure of the build as a whole
class BuildFailure(Exception):
    pass


class CommandGraph:
    tasks: List[_Task]

    def __init__(self):
        self.tasks = []

    def add(
        self,
        command: Sequence[CmdArgument],
        *,
        inputs: Sequence[Union[Path, str]],
        outputs: Sequence[Union[Path, str]]
    ) -> None:

        self.tasks.append(
            _Task(
                command=command,
                inputs=[Path(input) for input in inputs],
                outputs=[Path(output) for output in outputs],
            )
        )
