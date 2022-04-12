import logging
from pathlib import Path
import re
import shlex
import subprocess
import time
from typing import List, Optional, Sequence

import ninja

from ._graph import CommandGraph, map_dict_values, resolve_placeholders
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


def write_ninja_file(g: CommandGraph, output):
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


def build_targets(g: CommandGraph, build_dir: Path, targets: Optional[Sequence[CmdArgument]], cwd: Optional[Path] = None):
    # targets = outputs | aliases
    if targets and not len(targets):
        return  # nothing to do

    build_dir.mkdir(exist_ok=True)
    ninjafile_path = build_dir / "build.ninja"

    pre = time.time()

    with open(ninjafile_path, "wt") as output:
        write_ninja_file(g, output)

    post = time.time()

    logger.info("write_ninja_file took %d msec", int((post - pre) * 1000))

    pre = time.time()
    extra_arguments = [str(x) for x in targets] if targets else []

    try:
        subprocess.check_call([Path(ninja.BIN_DIR) / "ninja", "-f", ninjafile_path.absolute()] + extra_arguments, cwd=cwd or build_dir)
    except subprocess.CalledProcessError as ex:
        raise BuildFailure(f"Ninja build returned error code {ex.returncode}") from None
    finally:
        post = time.time()

        logger.info("Ninja build took %d msec", int((post - pre) * 1000))

def build_all(g: CommandGraph, build_dir: Path, cwd: Optional[Path] = None):
    return build_targets(g, build_dir, targets=None, cwd=cwd)
