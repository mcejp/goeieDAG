import logging
from pathlib import Path
import re
import shlex
import subprocess
import time
from typing import List, Optional, Sequence

import ninja

from ._graph import Graph, map_dict_values, resolve_placeholders
from ._model import BuildFailure, CmdArgument


logger = logging.getLogger(__name__)


def _generate_rule_name(command: Sequence[CmdArgument], i: int) -> str:
    # try to extract something that represents the command intuitively (just for ninjafile debugging)
    blurb = " ".join(arg.name if isinstance(arg, Path) else str(arg) for arg in command)[:40]

    sanitized = _sanitize_rule_name(blurb)

    if not len(sanitized):
        sanitized = "rule"

    return f"{sanitized}_{i}"


# https://stackoverflow.com/a/23532381
_full_pattern = re.compile("[^a-zA-Z0-9_]|_")


def _sanitize_rule_name(string: str) -> str:
    return re.sub(_full_pattern, "_", string)


def write_ninja_file(g: Graph, output):
    writer = ninja.Writer(output)

    rule_names: List[str] = []

    # flatten everything
    flat_tasks = []
    for task in g.tasks:
        # Inputs/outputs must be shell-escaped before being substituted into the command.
        # This way, literal tokens in the command will be preserved, allowing use of shell features like output
        # redirections, but inserted input/output names will be sanitized.
        inputs_shellesc = map_dict_values(task.inputs, lambda path: shlex.quote(str(path)))
        outputs_shellesc = map_dict_values(task.outputs, lambda path: shlex.quote(str(path)))

        command = resolve_placeholders(task.command, inputs_shellesc, outputs_shellesc)

        flat_tasks.append((task.inputs, task.outputs, command))

    # generate rules
    for inputs, outputs, command in flat_tasks:
        rule_name = _generate_rule_name(command, len(rule_names))
        rule_names.append(rule_name)

        writer.rule(
            name=rule_name,
            command=" ".join(ninja.escape(str(arg)) for arg in command),
        )
        writer.newline()

    # emit build statements
    for i, (inputs, outputs, command) in enumerate(flat_tasks):
        writer.build(
            rule=rule_names[i],
            inputs=[str(i) for i in inputs.values()],
            outputs=[str(i) for i in outputs.values()],
        )
        writer.newline()

        if len(outputs):
            writer.default([str(i) for i in outputs.values()])
            writer.newline()

    # emit Phony statements for aliases
    for name, inputs_list in g.aliases.items():
        writer.build(rule="phony", inputs=[str(i) for i in inputs_list], outputs=[name])

    writer.close()
    del writer


def build_targets(g: Graph, build_dir: Path, targets: Optional[Sequence[CmdArgument]], cwd: Optional[Path] = None):
    """
    Build the given targets.

    :param g: a graph
    :type g: Graph
    :param build_dir: A directory which will be used for build-related files (Ninja file, etc.)
    :type build_dir: Path
    :param targets: A set of previously declared targets (outputs or aliases) to build.
    :type targets: sequence of str and/or Path
    :param cwd: Working directory for the build. Any relative paths specified in the graph will be relative to this directory.
                If not specified, `build_dir` will be used.
    :type cwd: Path or None
    """

    # targets = outputs | aliases
    if targets is not None and len(targets) == 0:
        return  # nothing to do

    build_dir.mkdir(exist_ok=True)
    ninjafile_path = build_dir / "build.ninja"

    pre = time.time()

    with open(ninjafile_path, "wt") as output:
        write_ninja_file(g, output)

    post = time.time()

    logger.info("write_ninja_file took %d msec", int((post - pre) * 1000))

    pre = time.time()

    if targets is not None:
        extra_arguments = [str(x) for x in targets]
    else:
        extra_arguments = []  # build all targets

    try:
        subprocess.check_call([Path(ninja.BIN_DIR) / "ninja", "-f", ninjafile_path.absolute()] + extra_arguments, cwd=cwd or build_dir)
    except subprocess.CalledProcessError as ex:
        raise BuildFailure(f"Ninja build returned error code {ex.returncode}") from None
    finally:
        post = time.time()

        logger.info("Ninja build took %d msec", int((post - pre) * 1000))


def build_all(g: Graph, build_dir: Path, cwd: Optional[Path] = None):
    """
    Build all targets in the given graph.

    :param g: a graph
    :type g: Graph
    :param build_dir: A directory which will be used for build-related files (Ninja file, etc.)
    :type build_dir: Path
    :param cwd: Working directory for the build. Any relative paths specified in the graph will be relative to this directory.
                If not specified, `build_dir` will be used.
    :type cwd: Path or None
    """

    return build_targets(g, build_dir, targets=None, cwd=cwd)
