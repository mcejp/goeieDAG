from pathlib import Path
import tempfile

import goeiedag
from goeiedag import ALL_INPUTS, INPUT, OUTPUT


def test_basic():
    with tempfile.TemporaryDirectory() as dir:
        graph = goeiedag.Graph()

        # Extract OS name from /etc/os-release
        graph.add(["grep", "^NAME=", INPUT, ">", OUTPUT],
                  inputs=["/etc/os-release"],
                  outputs=["os-name.txt"])
        # Get username
        graph.add(["whoami", ">", OUTPUT],
                  inputs=[],
                  outputs=["username.txt"])
        # Glue together to produce output
        graph.add(["cat", ALL_INPUTS, ">", OUTPUT.result],
                  inputs=["os-name.txt", "username.txt"],
                  outputs=dict(result="result.txt"))

        goeiedag.build_all(graph, Path(dir))

        assert (Path(dir) / "result.txt").stat().st_size > 0


def test_escape():
    with tempfile.TemporaryDirectory() as dir:
        graph = goeiedag.Graph()

        graph.add(["echo", "Hello", ">", OUTPUT], inputs=[], outputs=[">weirdfilename"])

        goeiedag.build_all(graph, Path(dir))

        assert (Path(dir) / ">weirdfilename").stat().st_size > 0


def test_alias():
    with tempfile.TemporaryDirectory() as dir:
        graph = goeiedag.Graph()

        graph.add(["echo", "Hello", ">", OUTPUT], inputs=[], outputs=["file1"])
        graph.add(["echo", "Hello", ">", OUTPUT], inputs=[], outputs=["file2"])
        graph.add(["echo", "Hello", ">", OUTPUT], inputs=[], outputs=["file3"])
        graph.add_alias("file1", Path("file3"), name="files1_3")

        goeiedag.build_targets(graph, Path(dir), ["files1_3"])

        assert (Path(dir) / "file1").exists()
        assert not (Path(dir) / "file2").exists()
        assert (Path(dir) / "file3").exists()


def test_outputs_dict():
    with tempfile.TemporaryDirectory() as dir:
        graph = goeiedag.Graph()

        graph.add(["touch", OUTPUT.foo], inputs=[], outputs=dict(foo="file1"))
        graph.add(["touch", OUTPUT.foo], inputs=[], outputs=dict(foo="file2"))

        goeiedag.build_all(graph, Path(dir))
