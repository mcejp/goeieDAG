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


class Graph:
    """
    This class is used to define the graph of inputs, outputs and the processing steps in between.

    A graph defines a set of *targets*, each being either an output of a :py:meth:`command <add>`,
    or an :py:meth:`alias <add_alias>`.
    """

    aliases: Dict[str, Sequence[Path]]  #: :meta private:
    tasks: List[_Task]                  #: :meta private:

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
        """
        Define how the given inputs are transformed into outputs.

        The command, its arguments, inputs and outputs can be any combination of ``str`` and ``Path``.

        :param command: The command and its arguments.
                        May contain input/output :ref:`placeholders <placeholders>`.
        :type command: sequence
        :param inputs: Inputs to the command, as a sequence or dict with ``str`` keys.
        :type inputs: sequence or dict
        :param outputs: Outputs of the command, as a sequence or dict with ``str`` keys.
        :type outputs: sequence or dict


        :Example:

        Concatenate two files to produce a third one::

            graph.add(["cat", ALL_INPUTS, ">", OUTPUT.result],
                      inputs=["os-name.txt", "username.txt"],
                      outputs=dict(result="result.txt"))
        """

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
        """
        Create an alias target. Building this target will build all the targets named as arguments.

        :param args: One or more targets.
        :type args: sequence of str and/or Path
        :param name: Optional name of the alias. If not provided, a unique name will be assigned.
        :type name: str or None
        :return: The name of the new alias.
        :rtype: str
        """

        if name is None:
            name = f"_alias_{len(self.aliases)}"

        assert name not in self.aliases
        self.aliases[name] = [Path(arg) for arg in args]
        return name
