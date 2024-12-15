.. raw:: pdf

  PageBreak appendixPage

.. _appendix-a:

About Extensions
++++++++++++++++

Since version 2.1 `ViTables` has a simple but powerful extensions framework.

If you are interested in writing extensions the next paragraphs can be of utility. If not you can skip to the list of available extensions.

Extensions live in the extensions subdirectory of the root directory where the source code is installed. An extension can be a pure Python module or can have a package structure (i.e. a directory with a :mod:`__init__.py` file). Packages can have as many directories as you want but extensions must be located at top level of the package.

The use of contracts is not enforced when writing extensions so you have nearly complete freedom for writing them. Nevertheless an extension must declare the following two variables:
:const:`ext_name` which is set to the descriptive name of the extension and will be used in the Extensions page of the Preferences dialog and :const:`comment` which is set to a short description of the extension and will be used too in the Extensions page of the Preferences dialog.

In some cases it can be useful to use convenience variables or methods. For instance, suppose than in the Preferences dialog you want to show a more complete description of your extension that that provided by the :const:`comment` variable. Then you may be interested in define a method :meth:`helpAbout` in your extension.

Of course some knowledge (not necessarily a deep one) of the `ViTables` code is required in order to bind your extension to the application core. This task is commonly achieved via the menu bar of the main window or via the signals/slots mechanism (convenience signals can be defined in the application if needed).

If you need more help just send an email to developers or ask to the `ViTables` Users' Group.

Three extensions are currently distributed along with the application:

  Time series formatter
    formats time series in a human friendly way. It supports PyTables time datatypes and PyTables time series created via `pandas <https://pandas.pydata.org>`_ or the obsolete scikits.timeseries module. The format used for displaying times can be configured by user via the Preferences dialog or editing by hand the :file:`time_format.ini` configuration file.

  Tree of DBs sorting
    sorts the display of the databases tree.

  Columnar organization of arrays
    rearranges several arrays with the same number of rows and displays them in a unique widget.
