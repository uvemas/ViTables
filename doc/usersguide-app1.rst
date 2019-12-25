.. raw:: pdf

  PageBreak appendixPage

.. _appendix-a:

About Plugins
+++++++++++++

Since version 2.1 `ViTables` has a simple but powerful plugins framework.

If you are interested in writing plugins the next paragraphs can be of utility. If not you can skip to the list of available plugins.

Plugins live in the plugins subdirectory of the root directory where the source code is installed. A plugin can be a pure Python module or can have a package structure (i.e. a directory with a :mod:`__init__.py` file). Packages can have as many directories as you want but plugins must be located at top level of the package.

The use of contracts is not enforced when writing plugins so you have nearly complete freedom for writing them. Nevertheless a plugin must declare the following variables. :const:`plugin_class` which is set to the name of the class invoqued when your plugin is executed by `ViTables`,
:const:`plugin_name` which is set to the descriptive name of the plugin and will be used in the Plugins page of the Preferences dialog and, finally, :const:`comment` which is set to a short description of the plugin and will be used too in the Plugins page of the Preferences dialog.

In some cases it can be useful to use convenience variables or methods. For instance, suppose than in the Preferences dialog you want to show a more complete description of your plugin that that provided by the :const:`comment` variable. Then you may be interested in define a method :meth:`helpAbout` in your plugin.

Of course some knowledge (not necessarily a deep one) of the `ViTables` code is required in order to bind your plugin to the application core. This task is commonly achieved via the menu bar of the main window or via the signals/slots mechanism (convenience signals can be defined in the application if needed).

If you need more help just send an email to developers or ask to the `ViTables` Users' Group.

Three plugins are currently distributed along with the application:

  Time series formatter
    formats time series in a human friendly way. It supports PyTables time datatypes and PyTables time series created via `pandas <https://pandas.pydata.org>`_ or the obsolete scikits.timeseries module. The format used for displaying times can be configured by user via the Preferences dialog or editing by hand the :file:`time_format.ini` configuration file.

  Tree of DBs sorting
    sorts the display of the databases tree.

  Columnar organization of arrays
    rearranges several arrays with the same number of rows and displays them in a unique widget.
