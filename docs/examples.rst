Examples
========

This example shows usage of the Eva object, used for controlling Eva, reading Eva's current state and responding to different events triggered by Eva's operation.

.. literalinclude:: ../examples/eva_example.py


This example shows usage of the eva_ws and eva_http modules, used for direct control using the network interfaces. eva_http also contains some helper functions not contained in the public API, such as lock_wait_for.

.. literalinclude:: ../examples/http_ws_example.py
