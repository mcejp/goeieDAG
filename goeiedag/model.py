from dataclasses import dataclass
from pathlib import Path
from typing import List, Union, Sequence


class _Input:
    pass


class _Output:
    pass


CmdArgument = Union[Path, str]
ALL_INPUTS = _Input()
ALL_OUTPUTS = _Output()
INPUT = _Input()  # unique input (asserted)
OUTPUT = _Output()   # unique output (asserted)


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
        command: Sequence[Union[CmdArgument, _Input, _Output]],
        *,
        inputs: Sequence[Union[Path, str]],
        outputs: Sequence[Union[Path, str]]
    ) -> None:
        command_expanded: List[Union[CmdArgument]] = []

        for arg in command:
            if arg is ALL_INPUTS:
                command_expanded += inputs
            elif arg is ALL_OUTPUTS:
                command_expanded += outputs
            elif isinstance(arg, _Input):
                assert len(inputs) == 1
                command_expanded += inputs
            elif isinstance(arg, _Output):
                assert len(outputs) == 1
                command_expanded += outputs
            else:
                command_expanded.append(arg)

        self.tasks.append(
            _Task(
                command=command_expanded,
                inputs=[Path(input) for input in inputs],
                outputs=[Path(output) for output in outputs],
            )
        )
