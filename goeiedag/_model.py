import collections
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence


@dataclass
class _PlaceholderBase:
    name: Optional[str]
    prefix: str = ""

    def __getattr__(self, name: str) -> "_PlaceholderBase":
        assert self.name == ""
        return self.__class__(name)

    def __radd__(self, other: str) -> "_PlaceholderBase":
        if not isinstance(other, str):
            raise TypeError()

        return self.__class__(name=self.name, prefix=other + self.prefix)


class _Input(_PlaceholderBase):
    pass


class _Output(_PlaceholderBase):
    pass


CmdArgument = Path | str
ALL_INPUTS = _Input(None)
ALL_OUTPUTS = _Output(None)
INPUT = _Input("")  # unique input (asserted)
OUTPUT = _Output("")   # unique output (asserted)


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
        command: Sequence[CmdArgument | _Input | _Output],
        *,
        inputs: Sequence[Path | str] | Dict[str, Path | str],
        outputs: Sequence[Path | str] | Dict[str, Path | str]
    ) -> None:
        command_expanded: List[CmdArgument] = []

        for arg in command:
            if isinstance(arg, _Input):
                if arg.name is None:  # All inputs
                    assert arg.prefix == ""
                    assert isinstance(inputs, collections.abc.Sequence)

                    command_expanded += inputs
                elif arg.name == "":  # Unique input
                    assert len(inputs) == 1

                    command_expanded.append(arg.prefix + str(inputs[0]))
                else:  # Specific input
                    assert arg.name is not None
                    assert isinstance(inputs, dict)

                    command_expanded.append(arg.prefix + str(inputs[arg.name]))
            elif isinstance(arg, _Output):
                if arg.name is None:  # All outputs
                    assert arg.prefix == ""
                    assert isinstance(outputs, collections.abc.Sequence)

                    command_expanded += outputs
                elif arg.name == "":  # Unique output
                    assert len(outputs) == 1

                    command_expanded.append(arg.prefix + str(outputs[0]))
                else:  # Specific output
                    assert arg.name is not None
                    assert isinstance(outputs, dict)

                    command_expanded.append(arg.prefix + str(outputs[arg.name]))
            else:
                command_expanded.append(arg)

        inputs_sequence = inputs.values() if isinstance(inputs, dict) else inputs
        outputs_sequence = outputs.values() if isinstance(outputs, dict) else outputs

        self.tasks.append(
            _Task(
                command=command_expanded,
                inputs=[Path(input) for input in inputs_sequence],
                outputs=[Path(output) for output in outputs_sequence],
            )
        )
