Quickstart
==========

样例代码

.. code-block:: python

  #!/usr/bin/env python
  # coding: utf-8
  from moa import moa

  moa.set_serialno('cff*') # 支持通配符
  moa.set_address(('localhost', 5037)) # adbd默认监听5037端口

  moa.touch('start.png')

.. note::
  连接设备还可以使用connect ``moa.connect('moa://localhost:5037/cff*')``
