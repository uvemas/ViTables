
.. _configuration-chapter:

Configuring ViTables
====================

As mentioned earlier, many aspects of the *ViTables* behaviour can
be customized by you through the
:menuselection:`Settings --> Preferences`
command.

It shows a dialog offering you several customization
possibilities. The dialog is made of three stacked pages,
:guilabel:`General`, :guilabel:`Look & Feel` and
:guilabel:`Plugins`.

The :guilabel:`General` page allows to change the
*ViTables* behavior at startup. You can set the
initial working directory to be that one from which *ViTables* is starting or
to be the last used
working directory. And you can recover your last working session.

The :guilabel:`Look & Feel` page allows to change visual
aspects of the application such as fonts, colors or even the general style,
so you can adapt the global aspect of *ViTables*
to what would be expected on your platform.

From the :guilabel:`Plugins` page the plugins can be managed. You
can add or remove searching paths for plugins and enable or disable the available
plugins

The :guilabel:`OK` button will apply the new settings and
make them permanent by saving them in the Windows registry, in a
configuration file (on Unix platforms) or in a plist file (on Mac OS X platforms). Even
if settings are stored in a plain text file editing it by hand is not
recommended. Some settings, like fonts or geometry settings [#f3]_, are stored in a way not really intended to be modified manually.

The configuration file is divided into sections, labeled as
[section_name]. Every section is made of subsections
written as key/value pairs and representing the item that is being
customized.
Currently the following sections/subsections are available:

.. glossary::

  [Geometry] HSplitter
    the size of the horizontal splitter

  [Geometry] Layout
    the position and size of toolbars and dock widgets

  [Geometry] Position
    the position and size of the application window

  [Geometry] VSplitter
    the size of the vertical splitter

  [HelpBrowser] Bookmarks
    the list of current bookmarks of the help browser

  [HelpBrowser] History
    the navigation history of the help browser

  [Logger] Font
    the logger font

  [Logger] Paper
    the logger background color

  [Logger] Text
    the logger text color

  [Look] currentStyle
    the style that defines the application look & feel. Available styles fit the most common platforms, i.e., Windows, Unix (Motif and SGI flavors), and Macintosh

  [Plugins] Enabled
    the list of full paths of enabled plugins

  [Plugins] Paths
    the list of paths where plugins will be searched

  [Recent] Files
    the list of files recently opened

  [Session] Files
    the list of files and views that were open the last time *ViTables* was closed

  [Startup] lastWorkingDir
    the last directory accessed from within *ViTables* via Open File dialog

  [Startup] restoreLastSession
    the last working session is restored (if possible) which means that both files and leaves that were open in the last session will be reopen at application startup.

  [Startup] startupWorkingDir
    possible values are *current*, and *last*. These values indicate how the application will setup the startup working directory.

  [Workspace] Background
    the workspace background brush

.. rubric:: Footnotes

.. [#f3] Entries in the Geometry section allow for keeping the aspect, size and position of the application window between sessions.

