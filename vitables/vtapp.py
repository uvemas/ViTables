#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2017 Vicent Mas. All rights reserved
#
#       This program is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#       Author:  Vicent Mas - vmas@vitables.org

"""
This module is the core of the application: it
controls the managers for specific tasks and contains the logic for reacting
to user's input i.e. the slots connected to every menu entry are defined here.
"""

import os
import time
import sys
import logging

import tables

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.utils
import vitables.filenodeutils as fnutils
import vitables.vtsplash
from vitables.vtsite import ICONDIR

from vitables.preferences import vtconfig
import vitables.preferences.pluginsloader as pluginsloader
from vitables.preferences import preferences

import vitables.queries.querymgr as qmgr

import vitables.vtwidgets.nodenamedlg as nodenamedlg
import vitables.vtwidgets.renamedlg as renamedlg

from vitables.docbrowser import helpbrowser

import vitables.vttables.datasheet as datasheet

import vitables.csv.import_csv as importcsv
import vitables.csv.export_csv as exportcsv

import vitables.vtgui as vtgui

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate
log = logging.getLogger(__name__)


def _makePage(content):
    """Create a page for the About ViTables dialog.

    :Parameter content: the text displayed on the page
    """

    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())
    text_edit = QtWidgets.QTextEdit(widget)
    text_edit.setReadOnly(1)
    text_edit.setAcceptRichText(True)
    text_edit.setText(content)
    widget.layout().addWidget(text_edit)

    return widget


class VTApp(QtCore.QObject):
    """
    The application core.

    :Parameters:

    - `mode`: the opening mode for files passed in the command line
    - `h5files`: a list of files to be open at startup
    - `dblist`: a file that contains a list of files to be open at startup
    """
    # Convenience signals for the plugins. Usually new signals are added
    # when a new plugin is added to ViTables. They are the link between
    # the plugins and the core of the program
    leaf_model_created = QtCore.Signal(QtWidgets.QMdiSubWindow,
                                       name="leafModelCreated")
    dbtree_model_created = QtCore.Signal()
    pluginsLoaded = QtCore.Signal()

    def __init__(self, mode='', dblist='', h5files=None, keep_splash=True):
        """
        Initialize the application.

        This method starts the application: makes the GUI, configure the
        app, instantiates managers needed to control the app. and connect
        signals to slots.
        """

        super(VTApp, self).__init__()

        # Make the main window easily accessible for external modules
        self.setObjectName('VTApp')

        self.is_first_opening = True  # for Open file dialogs

        # Show a splash screen
        logo = QtGui.QPixmap(os.path.join(ICONDIR, "vitables_logo.png"))
        splash = vitables.vtsplash.VTSplash(logo)
        splash.show()
        t_i = time.time()

        # Create the GUI. This is done in 3 steps:
        # - create the main window
        # - create the model/view for the tree of databases
        # - setup the main window
        splash.drawMessage(translate('VTApp', 'Creating the GUI...',
                                     'A splash screen message'))
        self.gui = vtgui.VTGUI(self, vtconfig.getVersion())

        # Apply the configuration stored on disk
        splash.drawMessage(translate('VTApp', 'Configuration setup...',
                                     'A splash screen message'))

        # Instantiate a configurator object for the application
        self.config = vtconfig.Config()
        self.config.applyConfiguration(self.config.readConfiguration())

        # Add import/export CSV capabilities
        self.csv_importer = importcsv.ImportCSV()
        self.csv_exporter = exportcsv.ExportToCSV()

        # Load plugins.
        # Some plugins modify existing menus so plugins must be loaded after
        # creating the user interface.
        # Some plugins modify the tree of databases or datasets displaying so
        # plugins must be loaded before opening any file.
        self.plugins_mgr = \
            pluginsloader.PluginsLoader(self.config.enabled_plugins)
        self.plugins_mgr.loadAll()
        self.pluginsLoaded.emit()
        self.dbtree_model_created.emit()

        # The queries manager
        self.queries_mgr = qmgr.QueriesManager()

        # Print the welcome message
        self.gui.logger.write(
            translate('VTApp',
                      """ViTables {0}\nCopyright (c) 2008-2017 Vicent Mas."""
                      """\nAll rights reserved.""",
                      'Application startup message').format(
                          vtconfig.getVersion()))

        # The list of most recently open DBs
        self.number_of_recent_files = 10
        while len(self.config.recent_files) > self.number_of_recent_files:
            del self.config.recent_files[-1]

        # The File Selector History
        self.file_selector_history = []
        if self.config.initial_working_directory != 'last':
            # Reset the last working directory if the Session/startupWorkingDir
            # setting is not 'last'
            self.config.last_working_directory = os.getcwd()
        self.file_selector_history.append(self.config.last_working_directory)

        # List of HelpBrowser instances in memory
        self.doc_browser = None

        # Restore last session
        if self.config.restore_last_session:
            splash.drawMessage(translate('VTApp', 'Recovering last session...',
                                         'A splash screen message'))
            self.recoverLastSession()

        # Process the command line
        if h5files:
            splash.drawMessage(translate('VTApp', 'Opening files...',
                                         'A splash screen message'))
            self.processCommandLineArgs(mode=mode, h5files=h5files)
        elif dblist:
            splash.drawMessage(translate('VTApp',
                                         'Opening the list of files...',
                                         'A splash screen message'))
            self.processCommandLineArgs(dblist=dblist)

        # Make sure that the splash screen is shown at least for two seconds
        if keep_splash:
            t_f = time.time()
            while t_f - t_i < 2:
                t_f = time.time()
        splash.finish(self.gui)
        del splash

        # Filenodes mappig
        self.filenodes_map = {}

        # Ensure that QActions have a consistent state
        self.gui.updateActions()

        self.gui.dbs_tree_model.rowsRemoved.connect(self.gui.updateActions)
        self.gui.dbs_tree_model.rowsInserted.connect(self.gui.updateActions)

        self.gui.updateWindowMenu()
    # Databases are automatically opened at startup when:
    #
    #     * application is configured for recovering last session
    #     * ViTables is started from the command line with some args
    #

    def recoverLastSession(self):
        """
        Recover the last session.

        This method will attempt to open those files and leaf views that
        were opened the last time the user closed ``ViTables``.
        The lists of files and leaves is read from the configuration
        file.
        The format is::

            ['mode#@#filepath1#@#nodepath1#@#nodepath2, ...',
            'mode#@#filepath2#@#nodepath1#@#nodepath2, ...', ...]
        """

        # Get the list of open files (temporary database is not included)
        for file_data in self.config.session_files_nodes:
            item = file_data.split('#@#')
            # item looks like [mode, filepath1, nodepath1, nodepath2, ...]
            mode = item.pop(0)
            filepath = item.pop(0)
            filepath = vitables.utils.forwardPath(filepath)
            # Open the database --> add the root group to the tree view.
            if self.gui.dbs_tree_model.openDBDoc(filepath, mode):
                self.gui.dbs_tree_view.setCurrentIndex(
                    self.gui.dbs_tree_model.index(0, 0, QtCore.QModelIndex()))
            db_doc = self.gui.dbs_tree_model.getDBDoc(filepath)
            if db_doc is None:
                continue
            # Update the history file
            self.updateRecentFiles(filepath, mode)

            # For opening a node the groups in the nodepath are expanded
            # left to right letting the lazy population feature to work
            for nodepath in item:  # '/group1/group2/...groupN/leaf'
                # Check if the node still exists because the database
                # could have changed since last ViTables session
                node = db_doc.get_node(nodepath)
                if node is None:
                    continue
                # groups is ['', 'group1', 'group2', ..., 'groupN']
                groups = nodepath.split('/')[:-1]
                # Expands the top level group, i.e., the root group.
                # It happens to be the last root node added to model
                # so its row is 0
                group = self.gui.dbs_tree_model.root.childAtRow(0)
                index = self.gui.dbs_tree_model.index(0, 0,
                                                      QtCore.QModelIndex())
                self.gui.dbs_tree_view.expanded.emit(index)
                groups.pop(0)
                # Expand the rest of groups of the nodepath
                while groups:
                    parent_group = group
                    parent_index = index
                    group = parent_group.findChild(groups[0])
                    row = group.row()
                    index = self.gui.dbs_tree_model.index(row, 0, parent_index)
                    self.gui.dbs_tree_view.expanded.emit(index)
                    groups.pop(0)
                # Finally we open the leaf
                leaf_name = nodepath.split('/')[-1]
                leaf = group.findChild(leaf_name)
                row = leaf.row()
                leaf_index = self.gui.dbs_tree_model.index(row, 0, index)
                self.gui.dbs_tree_view.setCurrentIndex(leaf_index)
                self.nodeOpen(leaf_index)

    def processCommandLineArgs(self, mode='', h5files=None, dblist=''):
        """
        Open files passed in the command line.

        :Parameters:

        - `mode`: the opening mode for files passed in the command line
        - `h5files`: a list of files to be open at startup
        - `dblist`: a file that contains a list of files to be open at startup
        """

        bad_line = translate('VTApp',
                             'Opening failed: wrong {0} in line {1} of {2}',
                             'Bad line format')
        # The database manager opens the files (if any)
        if isinstance(h5files, list):
            for filepath in h5files:
                filepath = vitables.utils.forwardPath(filepath)
                if self.gui.dbs_tree_model.openDBDoc(filepath, mode):
                    self.gui.dbs_tree_view.setCurrentIndex(
                        self.gui.dbs_tree_model.index(0, 0,
                                                      QtCore.QModelIndex()))
                    self.updateRecentFiles(filepath, mode)

        # If a list of files is passed then parse the list and open the files
        if dblist:
            try:
                input_file = open(dblist, 'r')
                lines = [i[:-1].split('#@#') for i in input_file.readlines()]
                input_file.close()
                for line in lines:
                    if line == ['']:
                        continue
                    if len(line) != 2:
                        log.error(bad_line.format('format', line,
                                                  dblist))
                        continue
                    [mode, filepath] = line
                    filepath = vitables.utils.forwardPath(filepath)
                    if mode not in ['r', 'a']:
                        log.error(bad_line.format('mode', line,
                                                  dblist))
                        continue
                    if self.gui.dbs_tree_model.openDBDoc(filepath, mode):
                        self.gui.dbs_tree_view.setCurrentIndex(
                            self.gui.dbs_tree_model.index(
                                0, 0, QtCore.QModelIndex()))
                        self.updateRecentFiles(filepath, mode)

            except IOError:
                log.error(
                    translate('VTApp', 'List of HDF5 files not read',
                              'File not updated error'))

    def updateRecentFiles(self, filepath, mode):
        """
        Add a new path to the list of most recently open files.

        :meth:`processCommandLineArgs`, :meth:`recoverLastSession`,
        :meth:`fileNew` and :meth:`fileOpen` call this method.

        :Parameters:

            - `filepath`: the last opened/created file
            - `mode`: the opening mode of the file
        """

        item = mode + '#@#' + filepath
        recent_files = self.config.recent_files
        # Updates the list of recently open files. Most recent goes first.
        if item not in recent_files:
            recent_files.insert(0, item)
        else:
            recent_files.remove(item)
            recent_files.insert(0, item)
        while len(recent_files) > self.number_of_recent_files:
            del recent_files[-1]

    def updateFSHistory(self, working_dir):
        """Update the navigation history of the file selector widget.

        :Parameter working_dir: the last visited directory
        """

        # Update the Session/lastWorkingDir setting
        self.config.last_working_directory = working_dir
        if working_dir not in self.file_selector_history:
            self.file_selector_history.append(working_dir)
        else:
            while working_dir in self.file_selector_history:
                self.file_selector_history.remove(working_dir)
            self.file_selector_history.append(working_dir)

    def fileNew(self):
        """Create a new file."""

        # Launch the file selector
        fs_args = {'accept_mode': QtWidgets.QFileDialog.AcceptOpen,
                   'file_mode': QtWidgets.QFileDialog.AnyFile,
                   'history': self.file_selector_history,
                   'label': translate('VTApp', 'Create',
                                      'Accept button text for QFileDialog')}
        filepath, working_dir = vitables.utils.getFilepath(
            self.gui,
            translate('VTApp', 'Creating a new file...',
                      'Caption of the File New... dialog'),
            dfilter=translate('VTApp',
                              """HDF5 Files (*.hdf *.h5 *.hd5 *.hdf5);;"""
                              """All Files (*)""",
                              'Filter for the Open New dialog'),
            settings=fs_args)

        if not filepath:
            # The user has canceled the dialog
            return

        # Update the history of the file selector widget
        self.updateFSHistory(working_dir)

        # Check the file extension
        filepath = vitables.utils.checkFileExtension(filepath)

        # Check the returned path
        if os.path.exists(filepath):
            log.error(
                translate('VTApp', 'New file creation failed because file '
                          'already exists.', 'A file creation error'))
            return

        # Open the database and select it in the tree view
        db_doc = self.gui.dbs_tree_model.createDBDoc(filepath)
        if db_doc:
            # The write mode must be replaced by append mode or the file
            # will be created from scratch in the next ViTables session
            self.gui.dbs_tree_view.setCurrentIndex(
                self.gui.dbs_tree_model.index(0, 0, QtCore.QModelIndex()))
            self.updateRecentFiles(filepath, 'a')

    def fileSaveAs(self):
        """
        Save a renamed copy of a file.

        This method exhibits the typical behavior: copied file is closed
        and the fresh renamed copy is opened.
        """

        overwrite = False
        current_index = self.gui.dbs_tree_view.currentIndex()

        # The file being saved
        initial_filepath = \
            self.gui.dbs_tree_model.nodeFromIndex(current_index).filepath

        # Launch the file selector
        fs_args = {'accept_mode': QtWidgets.QFileDialog.AcceptSave,
                   'file_mode': QtWidgets.QFileDialog.AnyFile,
                   'history': self.file_selector_history,
                   'label': translate('VTApp', 'Create',
                                      'Accept button text for QFileDialog')}
        trier_filepath, working_dir = vitables.utils.getFilepath(
            self.gui,
            translate('VTApp', 'Copying a file...',
                      'Caption of the File Save as... dialog'),
            dfilter=translate('VTApp',
                              """HDF5 Files (*.hdf *.h5 *.hd5 *.hdf5);;"""
                              """All Files (*)""",
                              'Filter for the Save As... dialog'),
            filepath=initial_filepath,
            settings=fs_args)

        if not trier_filepath:  # The user has canceled the dialog
            return

        # Update the history of the file selector widget
        self.updateFSHistory(working_dir)

        trier_filepath = vitables.utils.checkFileExtension(trier_filepath)

        #
        # Check if the chosen name is valid
        #

        info = [translate('VTApp', 'File Save as: file already exists',
                          'A dialog caption'), None]
        # Bad filepath conditions
        trier_dirname, trier_filename = os.path.split(trier_filepath)
        sibling = os.listdir(trier_dirname)
        filename_in_sibling = trier_filename in sibling
        is_tmp_filepath = \
            trier_filepath == self.gui.dbs_tree_model.tmp_filepath
        is_initial_filepath = trier_filepath == initial_filepath

        # If the suggested filepath is not valid ask for a new filepath
        # The loop is necessary because the file being saved as and the
        # temporary database can be in the same directory. In this case
        # we must check all error conditions every time a new name is tried
        while is_tmp_filepath or is_initial_filepath or filename_in_sibling:
            if is_tmp_filepath:
                info[1] = translate('VTApp',
                                    """Target directory: {0}\n\nThe Query """
                                    """results database cannot be """
                                    """overwritten.""",
                                    'Overwrite file dialog label').format(
                    trier_dirname)
                template = \
                    "(^{0}$)|[a-zA-Z_]+[0-9a-zA-Z_]*(?:\.[0-9a-zA-Z_]+)?$"
                pattern = template.format(trier_filename)
            elif is_initial_filepath:
                info[1] = translate('VTApp',
                                    """Target directory: {0}\n\nThe file """
                                    """being saved cannot overwrite itself.""",
                                    'Overwrite file dialog label').format(
                    trier_dirname)
                template = \
                    "(^{0}$)|[a-zA-Z_]+[0-9a-zA-Z_]*(?:\.[0-9a-zA-Z_]+)?$"
                pattern = template.format(trier_filename)
            elif filename_in_sibling:
                info[1] = translate('VTApp',
                                    """Target directory: {0}\n\nFile name {1}"""
                                    """ already in use in that directory.\n""",
                                    'Overwrite file dialog label').format(
                    trier_dirname, trier_filename)
                pattern = "[a-zA-Z_]+[0-9a-zA-Z_]*(?:\.[0-9a-zA-Z_]+)?$"

            dialog = renamedlg.RenameDlg(trier_filename, pattern, info)
            if dialog.exec_():
                trier_filename = dialog.action['new_name']
                trier_filepath = os.path.join(trier_dirname, trier_filename)
                trier_filepath = \
                    QtCore.QDir.fromNativeSeparators(trier_filepath)
                overwrite = dialog.action['overwrite']
                # Update the error conditions
                is_initial_filepath = trier_filepath == initial_filepath
                is_tmp_filepath = \
                    trier_filepath == self.gui.dbs_tree_model.tmp_filepath
                filename_in_sibling = trier_filename in sibling
                del dialog
                if (overwrite is True) and (not is_initial_filepath) and \
                        (not is_tmp_filepath):
                    break
            else:
                del dialog
                return

        filepath = vitables.utils.checkFileExtension(trier_filepath)

        # If an open file is overwritten then close it
        if overwrite and self.gui.dbs_tree_model.getDBDoc(filepath):
            for row, child in enumerate(self.gui.dbs_tree_model.root.children):
                if child.filepath == filepath:
                    self.fileClose(self.gui.dbs_tree_model.index(
                        row, 0, QtCore.QModelIndex()))
            # The current index could have changed when overwriting
            # so we update it
            for row in range(0,
                             self.gui.dbs_tree_model.rowCount(
                                 QtCore.QModelIndex())):
                index = QtCore.QModelIndex().child(row, 0)
                node = self.gui.dbs_tree_model.nodeFromIndex(index)
                if node.filepath == initial_filepath:
                    current_index = index
            self.gui.dbs_tree_view.setCurrentIndex(current_index)

        # Make a copy of the selected file
        try:
            QtWidgets.qApp.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.WaitCursor))
            dbdoc = self.gui.dbs_tree_model.getDBDoc(initial_filepath)
            dbdoc.copy_file(filepath)
        finally:
            QtWidgets.qApp.restoreOverrideCursor()

        # Close the copied file (which is not necessarely selected in
        # the tree view because closing an overwritten file can change
        # the selected item) and open the new copy in read-write mode.
        # The position in the tree is kept
        for row, child in enumerate(self.gui.dbs_tree_model.root.children):
            if child.filepath == initial_filepath:
                self.fileClose(self.gui.dbs_tree_model.index(
                    row, 0, QtCore.QModelIndex()))
                self.fileOpen(filepath, 'a', row)

    def fileOpenRO(self, filepath=None):
        """
        Open a file that contains a ``PyTables`` database in read-only mode.

        :Parameters filepath: the full path of the file to be open
        """
        self.fileOpen(filepath, mode='r')

    def openRecentFile(self):
        """
        Open the file selected in the `Open Recent...` submenu.
        """

        action = self.sender()
        item = action.data()
        (mode, filepath) = item.split('#@#')
        self.fileOpen(filepath, mode)

    def clearRecentFiles(self):
        """
        Clear the list of recently opened files and delete the corresponding
        historical file.
        """
        self.config.recent_files = []

    def fileOpen(self, filepath=None, mode='a', position=0):
        """
        Open a file that contains a ``PyTables`` database.

        If this method is invoqued via ``File -> Open`` then no filepath
        is passed and a dialog is raised. When the method is invoqued
        passing arguments to the command line or via
        :meth:`openRecentFile` or :meth:`fileSaveAs` methods then
        filepath is passed and the dialog is not raised.

        :Parameters:

        - `filepath`: the full path of the file to be open
        - `mode`: the file opening mode. It can be read-write or read-only
        - `position`: position in the tree view of the new file
        """

        if not filepath:
            # Launch the file selector
            fs_args = {'accept_mode': QtWidgets.QFileDialog.AcceptOpen,
                       'file_mode': QtWidgets.QFileDialog.ExistingFile,
                       'history': self.file_selector_history,
                       'label':
                       translate('VTApp', 'Open', 'Accept text for QFileDialog')
                       }
            filepath, working_dir = vitables.utils.getFilepath(
                self.gui,
                translate('VTApp', 'Select a file for opening',
                          'Caption of the File Open... dialog'),
                dfilter=translate('VTApp',
                                  """HDF5 Files (*.hdf *.h5 *.hd5 *.hdf5);;"""
                                  """All Files (*)""",
                                  'Filter for the Open New dialog'),
                settings=fs_args)

            if not filepath:
                # The user has canceled the dialog
                return

            # Update the history of the file selector widget
            self.updateFSHistory(working_dir)

        else:
            # Make sure filepath uses Unix-like separators
            filepath = vitables.utils.forwardPath(filepath)

        # Open the database and select it in the tree view
        if self.gui.dbs_tree_model.openDBDoc(filepath, mode, position):
            self.gui.dbs_tree_view.setCurrentIndex(
                self.gui.dbs_tree_model.index(
                    position, 0, QtCore.QModelIndex()))
            self.updateRecentFiles(filepath, mode)

    def fileClose(self, current=False):
        """
        Close a file.

        First of all this method finds out which database has to be closed.
        Afterwards all views belonging to that database are closed, then
        the object tree is removed from the databases tree and, finally, the
        database is closed.

        :Parameter current:
            the index in the databases tree of a node living in the file being
            closed
        """

        if current is False:
            current = self.gui.dbs_tree_view.currentIndex()
        node = self.gui.dbs_tree_model.nodeFromIndex(current)
        filepath = node.filepath

        # The position of this database in the tree view
        last_row = len(self.gui.dbs_tree_model.root.children) - 1
        for row, child in enumerate(self.gui.dbs_tree_model.root.children):
            if child.filepath == filepath:
                position = row
                break

        # If some leaf of this database has an open view then close it
        for window in self.gui.workspace.subWindowList():
            if window.dbt_leaf.filepath == filepath:
                window.close()

        # The tree model closes the file and delete its root item
        # from the tree view
        self.gui.dbs_tree_model.closeDBDoc(filepath)

        # The root node immediately below the closed node becomes selected
        if position <= last_row:
            index = self.gui.dbs_tree_model.index(position, 0,
                                                  QtCore.QModelIndex())
            self.gui.dbs_tree_view.setCurrentIndex(index)

    def fileCloseAll(self):
        """Close every open file."""

        # The list of top level items to be removed.
        # The temporary database should be closed at quit time only
        open_files = len(self.gui.dbs_tree_model.root.children) - 1
        rows_range = list(range(0, open_files).__reversed__())
        # Reversing is a must because, if we start from 0, row positions
        # change as we delete rows
        for row in rows_range:
            index = self.gui.dbs_tree_model.index(row, 0, QtCore.QModelIndex())
            self.fileClose(index)

    def fileExit(self):
        """
        Safely close the application.

        Saves current configuration on disk, closes opened files and exits.
        """

        # Close all browsers
        if self.doc_browser:
            self.doc_browser.exitBrowser()
        # Save current configuration
        self.config.saveConfiguration()
        # Close every user opened file
        self.fileCloseAll()
        # Close the temporary database
        index = self.gui.dbs_tree_model.index(0, 0, QtCore.QModelIndex())
        self.fileClose(index)

    def tablesNode(self, index):
        """The tables.Leaf instance tied to the given index.

        :Parameter index: the tree of databases model index being retrieved
        """

        # The leaf (data structure) of the databases tree view tied to index
        leaf = self.gui.dbs_tree_model.nodeFromIndex(index)
        # The tables.Leaf instance referenced by that data structure
        pt_node = leaf.node
        if hasattr(pt_node, 'target'):
            return pt_node()
        return pt_node

    @vitables.utils.long_action("Opening node...")
    def nodeOpen(self, current=False):
        """
        Open a leaf node for viewing.

        :Parameter current: the index in the databases tree of the node being
            opened
        """

        if current is False:
            # Open the node currently selected in the tree of databases
            index = self.gui.dbs_tree_view.currentIndex()
        else:
            # When restoring the previous session explicit indexes are passed
            index = current
        leaf = self.tablesNode(index)

        # tables.UnImplemented datasets cannot be read so are not opened
        if isinstance(leaf, tables.UnImplemented):
            QtWidgets.QMessageBox.information(
                self.gui, translate('VTApp', 'About UnImplemented nodes',
                                    'A dialog caption'),
                translate('VTApp',
                          """Actual data for this node are not accesible."""
                          """<br> The combination of datatypes and/or """
                          """dataspaces in this node is not yet supported by """
                          """PyTables.<br>If you want to see this kind of """
                          """dataset implemented in PyTables, please, """
                          """contact the developers.""",
                          'Text of the Unimplemented node dialog'))
            return

        # Leaves that cannot be read are not opened
        if not vitables.utils.isDataSourceReadable(leaf):
            return

        # Track filenodes
        if fnutils.isFilenode(leaf) and (leaf not in self.filenodes_map):
            temp_filenode = fnutils.filenodeToFile(leaf)
            self.filenodes_map[leaf] = (temp_filenode,
                                        fnutils.filenodeTotalRows(leaf))

        # Create a view
        subwindow = datasheet.DataSheet(index)
        subwindow.show()

        # For unknown reasons sometimes views cannot be resized. This strange
        # problem is fixed by hiding the view and immediately showing it again
        subwindow.hide()
        subwindow.show()

        # Announcing the new view is potentially helpful for plugins in charge
        # of datasets customizations (for instance, additional formatting)
        self.leaf_model_created.emit(subwindow)

    def nodeClose(self, current=False):
        """
        Close the view of the selected node.

        The method is called by activating ``Node --> Close`` (what passes
        no argument) or programatically by the :meth:`fileClose`
        method (what does pass argument).
        If the target is an open leaf this method closes its view, delete
        its model and updates the controller tracking system.
        If the target node is a root group the method looks for opened
        children and closes them as described above.

        :Parameter current: the index in the databases tree of the node being
            closed
        """

        if not current:
            current = self.gui.dbs_tree_view.currentIndex()
        pcurrent = QtCore.QPersistentModelIndex(current)
        # Find out the subwindow tied to the selected node and close it
        for data_sheet in self.gui.workspace.subWindowList():
            if pcurrent == data_sheet.pindex:
                data_sheet.close()
                break

    def nodeNewGroup(self):
        """Create a new group node."""

        current = self.gui.dbs_tree_view.currentIndex()
        parent = self.gui.dbs_tree_model.nodeFromIndex(current)

        # Get the new group name
        dialog = nodenamedlg.InputNodeName(
            translate('VTApp', 'Creating a new group', 'A dialog caption'),
            translate('VTApp', 'Source file: {0}\nParent group: {1}\n\n ',
                      'A dialog label').format(parent.filepath,
                                               parent.nodepath),
            translate('VTApp', 'Create', 'A button label'))
        self.gui.editing_dlg = True
        if dialog.exec_():
            suggested_nodename = dialog.node_name
            self.gui.dbs_tree_view.setFocus(True)
            del dialog
        else:
            self.gui.dbs_tree_view.setFocus(True)
            del dialog
            return

        #
        # Check if the entered nodename is already in use
        #
        sibling = getattr(parent.node, '_v_children').keys()
        pattern = "[a-zA-Z_]+[0-9a-zA-Z_ ]*"
        info = [translate('VTApp',
                          'Creating a new group: name already in use',
                          'A dialog caption'),
                translate('VTApp',
                          """Source file: {0}\nParent group: {1}\n\nThere is """
                          """already a node named '{2}' in that parent group."""
                          """\n""",
                          'A dialog label').format
                (parent.filepath, parent.nodepath, suggested_nodename)]
        nodename, overwrite = vitables.utils.getFinalName(suggested_nodename,
                                                          sibling, pattern,
                                                          info)
        if nodename is None:
            return

        # If the creation overwrites a group with attached views then these
        # views are closed before the renaming is done
        if overwrite:
            nodepath = tables.path.join_path(parent.nodepath, nodename)
            self.gui.closeChildrenViews(nodepath, parent.filepath)

        self.gui.dbs_tree_model.create_group(current, nodename, overwrite)

    def nodeRename(self):
        """
        Rename the selected node.

        - ask for the node name
        - check the node name. If it is already in use ask what to
          do (possibilities are rename, overwrite and cancel creation)
        - rename the node
        """

        index = self.gui.dbs_tree_view.currentIndex()
        child = self.gui.dbs_tree_model.nodeFromIndex(index)
        parent = child.parent

        # Get the new nodename
        dialog = nodenamedlg.InputNodeName(
            translate('VTApp', 'Renaming a node', 'A dialog caption'),
            translate('VTApp', 'Source file: {0}\nParent group: {1}\n\n',
                      'A dialog label').format(parent.filepath,
                                               parent.nodepath),
            translate('VTApp', 'Rename', 'A button label'),
            child.name)
        self.gui.editing_dlg = True
        if dialog.exec_():
            suggested_nodename = dialog.node_name
            del dialog
        else:
            del dialog
            return

        #
        # Check if the nodename is already in use
        #
        sibling = getattr(parent.node, '_v_children').keys()
        # Note that current nodename is not allowed as new nodename.
        # Embedding it in the pattern makes unnecessary to pass it to the
        # rename dialog via method argument and simplifies the code
        pattern = """(^{0}$)|""" \
            """(^[a-zA-Z_]+[0-9a-zA-Z_ ]*)""".format(child.name)
        info = [translate('VTApp', 'Renaming a node: name already in use',
                          'A dialog caption'),
                translate('VTApp',
                          """Source file: {0}\nParent group: {1}\n\nThere is """
                          """already a node named '{2}' in that parent """
                          """group.\n""", 'A dialog label').format
                (parent.filepath, parent.nodepath, suggested_nodename)]
        nodename, overwrite = vitables.utils.getFinalName(suggested_nodename,
                                                          sibling, pattern,
                                                          info)
        self.gui.editing_dlg = True
        if nodename is None:
            return

        # If the renaming overwrites a node with attached views then these
        # views are closed before the renaming is done
        if overwrite:
            nodepath = tables.path.join_path(parent.nodepath, nodename)
            self.gui.closeChildrenViews(nodepath, child.filepath)

        # Rename the node
        self.gui.dbs_tree_model.rename_node(index, nodename, overwrite)

        # Update the Selected node indicator of the status bar
        self.gui.updateStatusBar()

    def nodeCut(self):
        """Cut the selected node."""

        current = self.gui.dbs_tree_view.currentIndex()

        # If the cut node has attached views then these views are closed
        # before the cutting is done. This behavior can be inconvenient
        # for users but get rid of potential problems that arise if, for
        # any reason, the user doesn't paste the cut node.
        node = self.gui.dbs_tree_model.nodeFromIndex(current)
        self.gui.closeChildrenViews(node.nodepath, node.filepath)

        # Cut the node
        self.gui.dbs_tree_model.cutNode(current)

    def nodeCopy(self):
        """
        Copy the selected node.
        """

        current = self.gui.dbs_tree_view.currentIndex()

        # Non readable leaves should not be copied
        dbs_tree_node = self.gui.dbs_tree_model.nodeFromIndex(current)
        if not (dbs_tree_node.node_kind in ('root group', 'group')):
            leaf = dbs_tree_node.node
            # tables.Leaf instances must be readable in order to be copied
            if not hasattr(leaf, 'target'):
                if not vitables.utils.isDataSourceReadable(leaf):
                    QtWidgets.QMessageBox.information(
                        self,
                        translate('VTApp', 'About unreadable datasets',
                                  'Dialog caption'),
                        translate('VTApp', """Sorry, actual data for this """
                                           """node are not accesible.<br>The """
                                           """node will not be copied.""",
                                  'Text of the Unimplemented node dialog'))
                    return

        # Copy the node
        self.gui.dbs_tree_model.copy_node(current)

    def nodePaste(self):
        """
        Paste the currently copied/cut node under the selected node.
        """

        current = self.gui.dbs_tree_view.currentIndex()
        parent = self.gui.dbs_tree_model.nodeFromIndex(current)

        cni = self.gui.dbs_tree_model.ccni
        if cni == {}:
            return

        nodename = cni['nodename']
        if cni['nodepath'] == '/':
            nodename = \
                'root_group_of_{0}'.format(os.path.basename(cni['filepath']))

        if cni['is_copied']:
            # Check if pasting a copied node is allowed (pasting a cut
            # node has no restrictions). It is not when
            # - source and target are the same node
            # - target is the source's parent
            if cni['filepath'] == parent.filepath:
                if (cni['nodepath'] == parent.nodepath) or \
                        (parent.nodepath == os.path.dirname(cni['nodepath'])):
                    return

        # Soft links cannot be pasted in external files
        if cni['target']:
            link = self.gui.dbs_tree_model.copiedNode()
            try:
                getattr(link, 'extfile')
            except AttributeError:
                if parent.filepath != cni['filepath']:
                    return

        #
        # Check if the nodename is already in use
        #
        sibling = getattr(parent.node, '_v_children').keys()
        # Nodename pattern
        pattern = "[a-zA-Z_]+[0-9a-zA-Z_ ]*"
        # Bad nodename conditions
        info = [translate('VTApp', 'Node paste: nodename already exists',
                          'A dialog caption'),
                translate('VTApp', """Source file: {0}\nCopied node: {1}\n"""
                          """Destination file: {2}\nParent group: {3}\n\n"""
                          """Node name '{4}' already in use in that group.\n""",
                          'A dialog label').format
                (cni['filepath'], cni['nodepath'], parent.filepath,
                 parent.nodepath, nodename),
                translate('VTApp', 'Paste', 'A button label')]
        # Validate the nodename
        nodename, overwrite = vitables.utils.getFinalName(nodename, sibling,
                                                          pattern, info)
        self.gui.editing_dlg = True
        if nodename is None:
            # Node editing dialog is not displayed
            return

        # If the pasting overwrites a node with attached views then these
        # views are closed before the pasting is done
        if overwrite:
            nodepath = tables.path.join_path(parent.nodepath, nodename)
            self.gui.closeChildrenViews(nodepath, parent.filepath)

        # Paste the node
        self.gui.dbs_tree_model.pasteNode(current, nodename, overwrite)

    def nodeDelete(self, current=False, force=None):
        """
        Delete a given node.

        :Parameters:

            - `current`: the index in the databases tree of the node being
              deleted
            - `force`: ask/do not ask for confirmation before deletion
        """

        if current is False:
            current = self.gui.dbs_tree_view.currentIndex()
        node = self.gui.dbs_tree_model.nodeFromIndex(current)

        # Confirm deletion dialog
        if not force:
            title = translate('VTApp', 'Node deletion',
                              'Caption of the node deletion dialog')
            text = translate('VTApp',
                             """\nYou are about to delete the node:\n{0}\n""",
                             'Ask for confirmation').format(node.nodepath)
            itext = ''
            dtext = ''
            buttons = {
                'Delete':
                    (translate('VTApp', 'Delete', 'Button text'),
                     QtWidgets.QMessageBox.YesRole),
                'Cancel':
                    (translate('VTApp', 'Cancel', 'Button text'),
                     QtWidgets.QMessageBox.NoRole),
            }

            # Ask for confirmation
            answer = \
                vitables.utils.questionBox(title, text, itext, dtext, buttons)
            self.gui.editing_dlg = True
            if answer == 'Cancel':
                return

        # If item is a filtered table then update the list of used names
        if hasattr(node.node._v_attrs, 'query_condition'):
            self.queries_mgr.ft_names.remove(node.name)

        # If the deletion involves a node with attached views then these
        # views are closed before the deletion is done
        self.gui.closeChildrenViews(node.nodepath, node.filepath)

        # Delete the node
        self.gui.dbs_tree_model.deleteNode(current)

        # Ensure that the new current node (if any) gets selected
        select_model = self.gui.dbs_tree_view.selectionModel()
        new_current = self.gui.dbs_tree_view.currentIndex()
        select_model.select(new_current, QtCore.QItemSelectionModel.Select)

    def nodeProperties(self):
        """
        Display the properties dialog for the currently selected node.

        The method is called by activating ``Node --> Properties``.
        """

        current = self.gui.dbs_tree_view.currentIndex()
        node = self.gui.dbs_tree_model.nodeFromIndex(current)
        node.properties()
        self.gui.editing_dlg = True

    def newQuery(self):
        """Slot for querying tables."""
        self.queries_mgr.newQuery()

    def deleteAllQueries(self):
        """Slot for emptying the `Query results` node."""
        self.queries_mgr.deleteAllQueries()

    def settingsPreferences(self):
        """
        Launch the Preferences dialog.

        Clicking the ``OK`` button applies the configuration set in the
        Preferences dialog.
        """

        prefs = preferences.Preferences()
        try:
            if prefs.exec_() == QtWidgets.QDialog.Accepted:
                self.config.applyConfiguration(prefs.new_prefs)
        finally:
            del prefs

    def windowClose(self):
        """Close the window currently active in the workspace."""

        self.gui.workspace.activeSubWindow().close()
        if not self.gui.workspace.subWindowList():
            self.gui.dbs_tree_view.setFocus(True)

    def windowCloseAll(self):
        """Close all open windows."""

        for window in self.gui.workspace.subWindowList():
            window.close()
        self.gui.dbs_tree_view.setFocus(True)

    def windowRestoreAll(self):
        """Restore every window in the workspace to its normal size."""

        for window in self.gui.workspace.subWindowList():
            window.showNormal()

    def windowMinimizeAll(self):
        """Restore every window in the workspace to its normal size."""

        for window in self.gui.workspace.subWindowList():
            window.showMinimized()

    def helpBrowser(self):
        """
        Open the documentation browser.
        """
        self.doc_browser = helpbrowser.HelpBrowser()

    def helpAbout(self):
        """
        Show a tabbed dialog with the application About and License info.
        """

        # Text to be displayed
        about_text = translate('VTApp', """<qt><h3>ViTables {0}</h3>
            ViTables is a graphical tool for displaying datasets
            stored in PyTables and HDF5 files. It is written using PyQt
            , the Python bindings for the Qt GUI toolkit.<p>
            For more information see
            <b>http://www.vitables.org</b>.<p>
            Please send bug reports or feature requests to the
            <em>ViTables Users Group</em>.<p>
            ViTables uses third party software which is copyrighted by
            its respective copyright holder. For details see the
            copyright notice of the individual packages.
            </qt>""", 'Text of the About ViTables dialog').format(
            vtconfig.getVersion())
        thanks_text = translate('VTApp', """<qt>
            Kostis Anagnostopoulos, Arne de Laat and Christoph Gohlke for 
            helping to revive ViTables with his great contributions.<p>
            Santi Villalba for the conda environment.<p>
            Alexey Naydenov for his contributions to the plugins system and for
            providing logging support to the application.<p>
            Robert Meyer, jaminsore, kprussing, Gaetan de Menten, Kamil Kisiel 
            and Max Bohnet for fixing bugs.<p>
            Dmitrijs Ledkovs for contributing the new and greatly enhanced
            build system and for making Debian packages.<p>
            Oxygen team for a wonderful icons set.<p>
            All the people who reported bugs and made suggestions.
            </qt>""", 'Text of the About ViTables dialog (Thanks to page)')
        license_text = vitables.utils.getLicense()

        # Construct the dialog
        about_dlg = QtWidgets.QDialog(self.gui)
        about_dlg.setWindowTitle(
            translate('VTApp', 'About ViTables {0}',
                      'Caption of the About ViTables dialog').
            format(vtconfig.getVersion()))
        layout = QtWidgets.QVBoxLayout(about_dlg)
        tab_widget = QtWidgets.QTabWidget(about_dlg)
        buttons_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        layout.addWidget(tab_widget)
        layout.addWidget(buttons_box)

        buttons_box.accepted.connect(about_dlg.accept)

        # Make About page
        content = [about_text, thanks_text, license_text]
        tabs = [translate('VTApp', '&About',
                          'Title of the first tab of the About dialog'),
                translate('VTApp', '&Thanks To',
                          'Title of the second tab of the About dialog'),
                translate('VTApp', '&License',
                          'Title of the third tab of the About dialog')]

        for index in range(0, 3):
            widget = _makePage(content[index])
            tab_widget.addTab(widget, tabs[index])

        # Show the dialog
        about_dlg.exec_()

    def helpAboutQt(self):
        """
        Show a message box with the Qt About info.
        """
        QtWidgets.QMessageBox.aboutQt(self.gui, translate(
            'VTApp', 'About Qt', 'Caption of the About Qt dialog'))

    def helpVersions(self):
        """
        Message box with info about versions of libraries used by
        ``ViTables``.
        """

        svi = sys.version_info
        pyversion = '.'.join((str(svi.major), str(svi.minor), str(svi.micro)))
        # The libraries versions dictionary
        libs_versions = {
            'title': translate('VTApp', 'Version Numbers',
                               'Caption of the Versions dialog'),
            'Python': pyversion,
            'PyTables': tables.__version__,
            'NumPy': tables.numpy.__version__,
            'Qt': QtCore.qVersion(),
            'PyQt': QtCore.PYQT_VERSION_STR,
            'ViTables': vtconfig.getVersion()
        }

        # Add new items to the dictionary
        libraries = ('HDF5', 'Zlib', 'LZO', 'BZIP2')
        for lib in libraries:
            lversion = tables.which_lib_version(lib.lower())
            if lversion:
                libs_versions[lib] = lversion[1]
            else:
                libs_versions[lib] = translate(
                    'VTApp', 'not available',
                    'Part of the library not found text')

        # Construct the dialog
        versions_dlg = QtWidgets.QDialog(self.gui)
        versions_dlg.setWindowTitle(translate('VTApp', 'Version Numbers',
                                              'Caption of the Versions dialog'))
        layout = QtWidgets.QVBoxLayout(versions_dlg)
        versions_edit = QtWidgets.QTextEdit(versions_dlg)
        buttons_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        layout.addWidget(versions_edit)
        layout.addWidget(buttons_box)

        buttons_box.accepted.connect(versions_dlg.accept)

        versions_edit.setReadOnly(1)
        versions_edit.setText(
            """
            <qt>
            <h3>{title}</h3>
            <table>
            <tr><td><b>Python</b></td><td>{Python}</td></tr>
            <tr><td><b>PyTables</b></td><td>{PyTables}</td></tr>
            <tr><td><b>NumPy</b></td><td>{NumPy}</td></tr>
            <tr><td><b>HDF5</b></td><td>{HDF5}</td></tr>
            <tr><td><b>Zlib</b></td><td>{Zlib}</td></tr>
            <tr><td><b>LZO</b></td><td>{LZO}</td></tr>
            <tr><td><b>BZIP2</b></td><td>{BZIP2}</td></tr>
            <tr><td><b>Qt</b></td><td>{Qt}</td></tr>
            <tr><td><b>PyQt</b></td><td>{PyQt}</td></tr>
            <tr><td><b>ViTables</b></td><td>{ViTables}</td></tr>
            </table>
            </qt>""".format(
                title=libs_versions['title'],
                Python=libs_versions['Python'],
                PyTables=libs_versions['PyTables'],
                NumPy=libs_versions['NumPy'],
                Qt=libs_versions['Qt'],
                PyQt=libs_versions['PyQt'],
                ViTables=libs_versions['ViTables'],
                HDF5=libs_versions['HDF5'],
                Zlib=libs_versions['Zlib'],
                LZO=libs_versions['LZO'],
                BZIP2=libs_versions['BZIP2'],
            ))

        # Show the dialog
        versions_dlg.exec_()
