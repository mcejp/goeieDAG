import collections
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypeVar, Union

from goeiedag._model import _Input, _Output, _PlaceholderBase, _Task, CmdArgument, InputsOutputs


K = TypeVar("K")
V = TypeVar("V")


def flatten_inputs_outputs(inputs, outputs) -> Tuple[Sequence, Sequence]:
    inputs_sequence = inputs.values() if isinstance(inputs, dict) else inputs
    outputs_sequence = outputs.values() if isinstance(outputs, dict) else outputs

    return inputs_sequence, outputs_sequence


def map_dict_values(collection: Dict[K, Any], callback: Callable[..., V]) -> Dict[K, V]:
    return {k: callback(v) for k, v in collection.items()}


def _ensure_dict(collection: Union[Sequence[V], Dict[K, V]]) -> Dict[Union[int, K], V]:
    if isinstance(collection, dict):
        # Mypy complains here about relaxing Dict[K, V] -> Dict[int | K, V]
        return collection  # type: ignore[return-value]
    else:
        return {i: v for i, v in enumerate(collection)}


def _resolve_placeholder(arg, mapping: dict) -> Sequence[str]:
    if arg.name is None:  # All inputs (outputs)
        assert arg.prefix == ""

        return list(mapping.values())
    elif arg.name == "":  # Unique input (output)
        assert len(mapping) == 1

        return [arg.prefix + str(mapping[0])]
    else:  # Specific input (output)
        assert arg.name is not None
        assert isinstance(mapping, dict)

        return [arg.prefix + str(mapping[arg.name])]


def resolve_placeholders(command: Sequence,
                         inputs: Dict[Union[int, str], str],
                         outputs: Dict[Union[int, str], str]) -> Sequence[CmdArgument]:
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
                inputs=map_dict_values(_ensure_dict(inputs), Path),
                outputs=map_dict_values(_ensure_dict(outputs), Path),
            )
        )

    def add_alias(self,
                  *args: Union[Path, str],
                  name: Optional[str] = None) -> str:
        if name is None:
            name = f"_alias_{len(self.aliases)}"

        assert name not in self.aliases
        self.aliases[name] = [Path(arg) for arg in args]
        return name
