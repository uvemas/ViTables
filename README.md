<div align=center>

![title_page_plain](doc/images/title_page_plain.svg)

![Platform](https://anaconda.org/conda-forge/vitables/badges/platforms.svg) ![License](https://anaconda.org/conda-forge/vitables/badges/license.svg)

![Conda](https://anaconda.org/conda-forge/vitables/badges/version.svg) ![Conda_downloads](https://anaconda.org/conda-forge/vitables/badges/downloads.svg) ![PyPI](https://img.shields.io/pypi/v/vitables) ![PyPI_Downloads](https://static.pepy.tech/badge/vitables/month)

</div>

# ViTables

ViTables is a component of the PyTables family. It is a GUI for browsing and editing files in both PyTables and HDF5 formats. It is developed using Python and PyQt5 (the Python bindings to Qt), so it can run on any platform that supports these components.

ViTables capabilities include easy navigation through the data hierarchy, displaying of real data and its associated metadata, a simple, yet powerful, browsing of multidimensional data and much more.

<div align=center>

![mainWindow](doc/images/mainWindow.png)

</div>

As a viewer, one of the greatest strengths of ViTables is its ability to display very large datasets. Tables with one thousand millions of rows (and beyond) are navigated stunningly fast and with very low memory requirements. So, if you ever need to browse huge tables, don't hesitate, ViTables is your choice.

If you need a customized browser for managing your HDF5 data, ViTables is an excellent starting point.

Here are some [screenshots](doc/images).

## QuickStart

### System requirements

ViTables 3.0.2 has been tested against the latest versions of Python 3,
PyTables and PyQt. You can try other versions at your own risk :).

### Install through pip (may need further manually debug)

```sh
$ pip install ViTables
```

If you may encounter `module 'collections' has no attribute 'Iterable'` error, simply change `collections.Iterable` to `collections.abc.Iterable` in line 152 and 180 of corresponding utils.py

### Install on a conda environment

Using conda you should be able to run vitables on any system, let it
be linux, mac or windows. The following are instructions for linux-like
systems.

Simply run

```sh
$ conda install -c conda-forge vitables
```

For more details, see [INSTALL.txt](INSTALL.txt).

### Launch

```sh
$ vitables [/path/to/hdf5/file]
```

If `/path/to/hdf5/file` is given, vitables will load that file, otherwise, you need to select a file to open later. 
