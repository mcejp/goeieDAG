# goeieDAG

goeieDAG provides a neutral Python API to Ninja and Make (_TODO_) build systems, aiming to
make it extremely easy to benefit from parallel processing in any graph-like workflow.


## Usage

```python
from pathlib import Path

import goeiedag

workdir = Path("output")
workdir.mkdir(exist_ok=True)

graph = goeiedag.CommandGraph()
# Get OS name
graph.add(["grep", "^NAME=", "/etc/os-release", ">", "os-name.txt"],
          inputs=["/etc/os-release"],
          outputs=["os-name.txt"])
# Get username
graph.add(["whoami", ">", "username.txt"],
          inputs=[],
          outputs=["username.txt"])
# Glue together to produce output
graph.add(["cat", "os-name.txt", "username.txt", ">", "result.txt"],
          inputs=["os-name.txt", "username.txt"],
          outputs=["result.txt"])

goeiedag.build_all(graph, workdir)

# Print output
print((workdir / "result.txt").read_text())
```


## Similar projects

- [Ninja](https://pypi.org/project/ninja/) (Python package) -- provides a lower-level API,
  used by goeieDAG as back-end
- [TaskGraph](https://github.com/natcap/taskgraph/) -- similar project, but centered around
  Python functions and in-process parallelism
- [Snakemake](https://snakemake.github.io/) -- similar goals, but a stand-alone tool rather
  than a library
- [Dask](https://dask.org/) -- different execution model, caching of intermediate results
  is left up to the user
- [doit](https://pydoit.org/)
