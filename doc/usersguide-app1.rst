
.. _appendix-a:

About Plugins
=============

Since version 2.1 *ViTables* has a simple but powerful plugins framework.

If you are interested in writing plugins the next paragraphs can be of utility. If not you can skip to the list of available plugins.

Plugins can live anywhere in your hard disk. A plugin can be a pure Python module or can have a package structure (i.e. a directory with a :mod:`__init__.py` file). Packages can have as many directories as you want but plugins must be located at top level of the package.

The use of contracts is not enforced for writing plugins so you have nearly complete freedom for writing. The only requirement that you must fulfil is to declare in your plugin a variable named :const:`plugin_class` and set it to the name of the class invoqued when your plugin is executed by *ViTables*.

In some cases it can be useful to use convenience variables or methods. For instance, if you are going to load the `Menu` plugin then you may be interested in declare the :const:`__version__` variable in your plugin. You can also consider to define methods :meth:`!configure` and/or :meth:`!helpAbout`.

Of course some knowledge (not necessarily a deep one) of the *ViTables* code is required in order to bind your plugin to the application core. This task is commonly achieved via the menu bar of the main window or via the signals/slots mechanism (convenience signals can be defined in the application if needed).

If you need more help just send an email to developers or ask to the *ViTables* Users' Group.

Three plugins are currently distributed along with the application:

.. glossary::

  Menu
    adds a :guilabel:`Plugins` menu to the menu bar. For every loaded plugin this menu has an entry from which a short description about the plugin is shown to users.

  Time series
    formats time series in a human friendly way. It supports PyTables time datatypes and PyTables time series created via scikits.timeseries module. The format used for displaying times can be configured by user via the `Menu` plugin or editing by hand the :file:`time_format.ini` configuration file.

  CSV
    provides import/export capabilities from/to :abbr:`CSV` files.

