import collections
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

from goeiedag._model import _Input, _Output, _PlaceholderBase, _Task, CmdArgument, InputsOutputsListOrDict


def flatten_inputs_outputs(inputs, outputs) -> Tuple[Sequence, Sequence]:
    inputs_sequence = inputs.values() if isinstance(inputs, dict) else inputs
    outputs_sequence = outputs.values() if isinstance(outputs, dict) else outputs

    return inputs_sequence, outputs_sequence


def map_values(collection: Union[Sequence[Path | str], Dict[str, Path | str]], callback: Callable):
    if isinstance(collection, dict):
        return {k: callback(v) for k, v in collection.items()}
    else:
        return [callback(v) for v in collection]


def _resolve_placeholder(arg, list_or_dict):
    if arg.name is None:  # All inputs
        assert arg.prefix == ""
        assert isinstance(list_or_dict, collections.abc.Sequence)

        return list_or_dict
    elif arg.name == "":  # Unique input
        assert isinstance(list_or_dict, collections.abc.Sequence)
        assert len(list_or_dict) == 1

        return [arg.prefix + str(list_or_dict[0])]
    else:  # Specific input
        assert arg.name is not None
        assert isinstance(list_or_dict, dict)

        return [arg.prefix + str(list_or_dict[arg.name])]


def resolve_placeholders(command: Sequence,
                         inputs: InputsOutputsListOrDict,
                         outputs: InputsOutputsListOrDict) -> Sequence[CmdArgument]:
    command_expanded: List[CmdArgument] = []

    for arg in command:
        if isinstance(arg, _Input):
            command_expanded += _resolve_placeholder(arg, inputs)
        elif isinstance(arg, _Output):
            command_expanded += _resolve_placeholder(arg, outputs)
        else:
            command_expanded.append(arg)

    return command_expanded


class CommandGraph:
    aliases: Dict[str, Sequence[Path]]
    tasks: List[_Task]

    def __init__(self):
        self.aliases = {}
        self.tasks = []

    def add(
            self,
            command: Sequence[CmdArgument | _PlaceholderBase],
            *,
            inputs: Sequence[Path | str] | Dict[str, Path | str],
            outputs: Sequence[Path | str] | Dict[str, Path | str]
    ) -> None:
        self.tasks.append(
            _Task(
                command=command,
                # From now on, all inputs/outpus must be Paths
                inputs=map_values(inputs, Path),
                outputs=map_values(outputs, Path),
            )
        )

    def add_alias(self,
                  *args: Union[Path, str],
                  name: Optional[str] = None) -> str:
        if name is None:
            name = f"_alias_{len(self.aliases)}"

        assert name not in self.aliases
        self.aliases[name] = map_values(args, Path)
        return name
