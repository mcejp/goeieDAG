from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


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
InputsOutputsListOrDict = Union[Dict[str, Path], Sequence[Path]]
ALL_INPUTS = _Input(None)
ALL_OUTPUTS = _Output(None)
INPUT = _Input("")  # unique input (asserted)
OUTPUT = _Output("")   # unique output (asserted)


@dataclass
class _Task:
    command: Sequence[Union[CmdArgument, _PlaceholderBase]]
    inputs: InputsOutputsListOrDict
    outputs: InputsOutputsListOrDict


# Deliberately not named BuildError, because it represents a non-specific failure of the build as a whole
class BuildFailure(Exception):
    pass
