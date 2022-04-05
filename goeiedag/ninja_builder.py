import logging
from pathlib import Path
import re
import subprocess
import time
from typing import List, Sequence

import ninja

from .model import BuildFailure, CmdArgument, CommandGraph


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


def build_all(g: CommandGraph, workdir: Path):

    with open(workdir / "build.ninja", "wt") as output:
        writer = ninja.Writer(output)

        rule_names: List[str] = []

        # generate rules
        for task in g.tasks:
            rule_name = _generate_rule_name(task.command, len(rule_names))
            rule_names.append(rule_name)

            writer.rule(
                name=rule_name,
                command=" ".join(ninja.escape(str(arg)) for arg in task.command),
            )
            writer.newline()

        # generate build statements
        for i, build in enumerate(g.tasks):
            writer.build(
                rule=rule_names[i],
                inputs=[str(i) for i in build.inputs],
                outputs=[str(i) for i in build.outputs],
            )
            writer.newline()

            if len(build.outputs):
                writer.default([str(i) for i in build.outputs])
                writer.newline()

        writer.close()
        del writer

    pre = time.time()

    try:
        subprocess.check_call([Path(ninja.BIN_DIR) / "ninja"], cwd=workdir)
    except subprocess.CalledProcessError as ex:
        raise BuildFailure(f"Ninja build returned error code {ex.returncode}") from None
    finally:
        post = time.time()

        logger.info("Ninja build took %d msec", int((post - pre) * 1000))
