# goeieDAG

_/ɣu.jə.ˈdɑx/: hello, good day (Dutch greeting used during daytime)_

goeieDAG provides a unified Python API to Ninja and Make (_TODO_) build systems, aiming to
make it extremely easy to benefit from parallel processing in any graph-like workflow.


## Usage

```python
from pathlib import Path

import goeiedag
from goeiedag import ALL_INPUTS, INPUT, OUTPUT

workdir = Path("output")

graph = goeiedag.CommandGraph()

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
          outputs=dict(result="result.txt"))  # can also use a dictionary and refer to inputs/outputs by name

goeiedag.build_all(graph, workdir)

# Print output
print((workdir / "result.txt").read_text())
```


## Q&A

### Why use the _files and commands_ model rather than _Python objects and functions_?

- It is a tested and proven paradigm (`make` traces back to _1976_!)
- It provides an obvious way of evaluating which products need rebuilding (subject to an
  accurate dependency graph)
- It naturally isolates and parallelizes individual build tasks
- It is agnostic as to how data objects are serialized (convenient for the library author...)
- Graph edges are implicitly defined by input/output file names
- A high-quality executor (Ninja) is available and installable via a Python package

### How is this different from using the Ninja package directly?

- Simpler mental model & usage: no need to separately define build rules or think about implicit/explicit inputs and
  outputs
- API accepts Paths; no need to cast everything to `str`!
- Higher-level API in general (for example, the output directory is created automatically)


## Similar projects

- [Ninja](https://pypi.org/project/ninja/) (Python package) -- provides a lower-level API,
  used by goeieDAG as back-end
- [TaskGraph](https://github.com/natcap/taskgraph/) -- similar project, but centered around
  Python functions and in-process parallelism
- [Snakemake](https://snakemake.github.io/) -- similar goals, but a stand-alone tool rather
  than a library
- [Dask](https://dask.org/) -- different execution model; caching of intermediate results
  is left up to the user
- [doit](https://pydoit.org/)
