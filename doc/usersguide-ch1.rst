.. |geq| unicode:: U+02265 .. greater than or equal symbol

Introduction
============



Overview
++++++++

*ViTables* is a member of the PyTables
family. It's a graphical tool for browsing and editing files in both
PyTables and :abbr:`HDF5` formats. With *ViTables* you
can easily navigate through data hierarchies, request metadata, view
real data and much more.

*ViTables* is being developed using Python
and PyQt, the bindings of Qt libraries, so it can run on any platform
that
supports these components (which includes Windows, Mac OS X, Linux and many
other Unices). The interface and features will remain the same on all
platforms.

Efficiency and low memory requirements are guaranteed by the fact
that data is loaded only when the object that contains it is opened and
by the use of data buffers for dealing with large datasets.

Capabilities
++++++++++++

The current release provides browsing, displaying, editing and querying capabilities. Some of them are listed
below. Details are discussed in the related chapters.

Browsing and Displaying Capabilities
************************************

- Display data hierarchy as a fully browsable object tree.

- Open several files simultaneously.

- Open files in write mode as well as in read-only mode, disabling all editing
  functions.

- Display file information (path, size, number of nodes…).

- Display node (group or leaf) properties, including metadata and attributes.

- Display numerical arrays, i.e. homogeneous tables.

- Display heterogeneous table entities, i.e. records.

- Display multidimensional table cells.

- Unlimited zoom into the inner dimensions of multidimensional table cells.

Editing Capabilities
********************

These editing features have been implemented for the object tree [#f1]_:

- File creation and renaming.

- Node creation (only for groups), renaming and deletion.

- Ability to copy and move nodes from their location to a different one, even in different files.

- Attribute creation, renaming and deletion.

All these changes automatically update the database (i.e. the file) to which the nodes belong.

Other
*****

Other nice features include:

- *Ability to smoothly navigate really large datasets*.

- Support for doing complex table queries with a low memory footprint.

- Flexible plugins framework. A bunch of useful plugins are already included, see the :ref:`Appendix A<appendix-a>` for
  details.

- Configurable look and feel.

- A logger area, where errors and warnings (if any) are printed.

- Several levels of help are available: users guide, context help, tooltips and status bar.

We have paid special attention to usability issues so making use of these features is intuitive and pleasant.
Nevertheless, and just in case, we are providing this guide :-).

System Requirements
+++++++++++++++++++

To run *ViTables* you need to install Python 2.6 or Python 2.7,
PyTables >= 2.2 (so you have to fulfil its own requirements) and PyQt4 >= 4.8.3.

At the moment, *ViTables* has been fully tested on Linux and Windows XP and Vista platforms.
Other Unices should run just fine when using the Linux version because all the
software that *ViTables* relies on (i.e. Python, Qt, PyQt, :abbr:`HDF5` and PyTables) is known to
run fine on many Unix platforms as well.

Installation
++++++++++++



Unix
****

The Distutils module (part of the standard
Python distribution) has
been used to prepare an installer for
*ViTables*. It makes easy to get the
application up and running.

At the moment no binary versions of the installer exist, so the
software has to be installed from sources.

Provided that your system fulfills the requirements listed in
the above sections, installing the package is really easy. Just
uncompress the package, change to the distribution directory and
execute

::

    $ python setup.py install

By default *ViTables* will be
installed
in the system-protected area where your system installs third party
Python packages, so you will need superuser privileges. If you prefer
to install the package in a different location (for instance, your
home directory, so that you can complete the installation as a
non-privileged user), you can do it using the
--prefix tag:

::

    $ python setup.py install --prefix=/home/myuser/mystuff

Please remember that installing Python modules in non-standard
locations makes it necessary to set the :envvar:`PYTHONPATH`
environment variable properly so that the Python interpreter can find
the installed modules.

If you need further customizations, please have a look at the
output of the command

::

    $python setup.py install --help

to see the available options. Complete information about these
options can be found in the Distutils documentation.

Windows Binary Installers
*************************

A binary installer is available for Windows platforms. Just double click the installer icon and follow
the wizard instructions. *ViTables* will be installed in a few clicks.

Beware that the installer is not a superpackage containing all *ViTables* requirements. You
need PyTables and PyQt4 already installed on your system (excellent installers for both packages are
available) in order to install *ViTables*.

Mac OS X Binary Installers
**************************

You can use the general Unix procedure to install
*ViTables* on Mac OS X, but
generating a double-clickable application bundle is
recommended. Simply untar the source package, change to the
distribution directory and execute

::

    $ cd macosxapp
    $ ./make.sh

If you have problems with this please, refer to the :abbr:`FAQ` page in the *ViTables* website.

Further Reading
***************

General information about PyTables can be found at the
project
site <www.pytables.com>.
For more information on :abbr:`HDF5`, please visit its
web site <www.hdfgroup.org/HDF5>.
Information about *ViTables* is available at 
<www.vitables.org>.

Questions and feedback can be mailed to the developers.

.. rubric:: Footnotes

.. [#f1] Dataset editing capabilities have not yet been implemented.

