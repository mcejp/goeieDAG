Introduction
============

Quickstart
----------

Install the package using *pip*:

.. code-block:: shell

    pip install goeieDAG


Here are some examples of usage:

.. code-block:: python

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


.. _placeholders:

Using placeholders
------------------

Placeholders can be used at any position in the argument sequence. These are the supported placeholders:

``INPUT``
  Substituted by the path to the input of the command.
  Invalid if multiple inputs were specified.

``INPUT.name``
  Substituted by the input called ``name``.
  Inputs must be specified as a dictionary.

``ALL_INPUTS``
  Expands to all inputs, as separate arguments.

``OUTPUT``
  Substituted by the path to the output of the command.
  Invalid if multiple outputs were specified.

``OUTPUT.name``
  Substituted by the output called ``name``.
  Outputs must be specified as a dictionary.

``ALL_OUTPUTS``
  Expands to all outputs, as separate arguments.


Prefixing placeholders
^^^^^^^^^^^^^^^^^^^^^^

Placeholders that refer to a single file (all except ``ALL_INPUTS``/``ALL_OUTPUTS``)
can also be combined with prefix strings, like this::

    # Get username
    graph.add(["whoami", ">" + OUTPUT],
            inputs=[],
            outputs=["username.txt"])
