# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2010 Vicent Mas. All rights reserved
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

"""Here is defined the VTApp class."""

__docformat__ = 'restructuredtext'
_context = 'VTApp'

import os
import time
import re
import sys

import tables

from PyQt4 import QtCore, QtGui

import vitables.utils
import vitables.vtsplash
from vitables.vtSite import ICONDIR

from  vitables.preferences import vtconfig
import vitables.preferences.pluginsLoader as pluginsLoader
from  vitables.preferences import preferences

import vitables.h5db.dbsTreeModel as dbsTreeModel
import vitables.h5db.dbsTreeView as dbsTreeView

import vitables.queries.queriesManager as qmgr

import vitables.vtWidgets.inputNodeName as inputNodeName
import vitables.vtWidgets.renameDlg as renameDlg

import vitables.nodeProperties.nodeInfo as nodeInfo
from vitables.nodeProperties import nodePropDlg
from vitables.docBrowser import helpBrowser

import vitables.vtTables.buffer as rbuffer
import vitables.vtTables.dataSheet as dataSheet

import vitables.vtGUI as vtGUI



def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


#class VTApp(QtGui.QMainWindow):
class VTApp(QtCore.QObject):
    """
    The application core.

    It handles the user input and controls both views and documents.
    VTApp methods can be grouped as:

    * GUI initialization and configuration methods
    * slots that handle user input
    """


    leaf_model_created = QtCore.pyqtSignal(QtGui.QMdiSubWindow, \
        name="leafModelCreated")

    pluginsLoaded = QtCore.pyqtSignal()


    def __init__(self, mode='', dblist='', h5files=None, keep_splash=True):
        """
        Initialize the application.

        This method starts the application: makes the GUI, configure the
        app, instantiates managers needed to control the app. and connect
        signals to slots.

        :Parameters:

        - `mode`: the opening mode for files passed in the command line
        - `h5files`: a list of files to be open at startup
        - `dblist`: a file that contains a list of files to be open at startup
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
        splash.drawMessage(trs('Creating the GUI...',
            'A splash screen message'))
        self.gui = vtGUI.VTGUI(self, vtconfig.getVersion())
        dbs_tmodel = dbsTreeModel.DBsTreeModel(self)
        dbsTreeView.DBsTreeView(self, dbs_tmodel)

        # The queries manager
        self.queries_mgr = qmgr.QueriesManager()

        # Instantiate a configurator object for the application
        self.config = vtconfig.Config()

        # Apply the configuration stored on disk
        splash.drawMessage(trs('Configuration setup...',
            'A splash screen message'))
        self.config.loadConfiguration(self.config.readConfiguration())

        # Print the welcome message
        print trs('''ViTables %s\nCopyright (c) 2008-2010 Vicent Mas.'''
            '''\nAll rights reserved.''' % vtconfig.getVersion(),
            'Application startup message')

        # The list of most recently open DBs
        self.number_of_recent_files = 10
        while self.config.recent_files.count() > self.number_of_recent_files:
            self.config.recent_files.takeLast()

        # The File Selector History
        self.file_selector_history = QtCore.QStringList()
        if self.config.startup_working_directory != u'last':
            self.config.last_working_directory = os.getcwdu()
        self.file_selector_history.append(self.config.last_working_directory)

        # List of HelpBrowser instances in memory
        self.doc_browser = None

        # Load plugins.
        # Some plugins modify existing menus so plugins must be loaded after
        # creating the user interface.
        # Some plugins modify datasets displaying so plugins must be loaded
        # before opening any file.
        self.plugins_mgr = \
            pluginsLoader.PluginsLoader(self.config.plugins_paths, 
            self.config.enabled_plugins)
        self.plugins_mgr.loadAll()
        self.pluginsLoaded.emit()

        # Restore last session
        if self.config.restore_last_session:
            splash.drawMessage(trs('Recovering last session...',
                'A splash screen message'))
            self.recoverLastSession()

        # Process the command line
        if h5files:
            splash.drawMessage(trs('Opening files...',
                'A splash screen message'))
            self.processCommandLineArgs(mode=mode, h5files=h5files)
        elif dblist:
            splash.drawMessage(trs('Opening the list of files...',
                'A splash screen message'))
            self.processCommandLineArgs(dblist=dblist)

        # Make sure that the splash screen is shown at least for two seconds
        if keep_splash:
            t_f = time.time()
            while t_f - t_i < 2:
                t_f = time.time()
        splash.finish(self.gui)
        del splash

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
        were opened the last time the user closed ViTables.
        The lists of files and leaves is read from the configuration.
        The format is::

            ['mode#@#filepath1#@#nodepath1#@#nodepath2, ...',
            'mode#@#filepath2#@#nodepath1#@#nodepath2, ...', ...]
        """

        for file_data in self.config.session_files_nodes:
            item = unicode(file_data).split('#@#')
            # item looks like [mode, filepath1, nodepath1, nodepath2, ...]
            mode = item.pop(0)
            filepath = item.pop(0)
            filepath = vitables.utils.forwardPath(filepath)
            # Open the database --> add the root group to the tree view.
            self.gui.dbs_tree_model.openDBDoc(filepath, mode)
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
                node = db_doc.getNode(nodepath)
                if node is None:
                    continue
                # groups is ['', 'group1', 'group2', ..., 'groupN']
                groups = nodepath.split('/')[:-1]
                # Expands the top level group, i.e., the root group.
                # It happens to be the last root node added to model
                # so its row is 0
                group = self.gui.dbs_tree_model.root.childAtRow(0)
                index = self.gui.dbs_tree_model.index(\
                    0, 0, QtCore.QModelIndex())
                self.gui.dbs_tree_view.expanded.emit(index)
                groups.pop(0)
                # Expand the rest of groups of the nodepath
                while groups != []:
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
        """Open files passed in the command line."""

        bad_line = trs("""Opening failed: wrong mode or path in %s""", 
                            'Bad line format')
        # The database manager opens the files (if any)
        if isinstance(h5files, list):
            for filepath in h5files:
                filepath = vitables.utils.forwardPath(filepath)
                self.gui.dbs_tree_model.openDBDoc(filepath, mode)
                self.updateRecentFiles(filepath, mode)

        # If a list of files is passed then parse the list and open the files
        if dblist:
            try:
                input_file = open(dblist, 'r')
                lines = [l[:-1].split('#@#') for l in input_file.readlines()]
                input_file.close()
                for line in lines:
                    if len(line) !=2:
                        print bad_line % line
                        continue
                    mode, filepath = line
                    filepath = vitables.utils.forwardPath(filepath)
                    if not mode in ['r', 'a']:
                        print bad_line % line
                        continue
                    self.gui.dbs_tree_model.openDBDoc(filepath, mode)
                    self.updateRecentFiles(filepath, mode)
            except IOError:
                print trs("""\nError: list of HDF5 files not read""",
                                'File not updated error')


    def updateRecentFiles(self, filepath, mode):
        """
        Add a new path to the list of most recently open files.

        ``processCommandLineArgs``, ``recoverLastSession``, ``fileNew``,
        and ``fileOpen`` call this method.

        :Parameters:

            - `filepath`: the last opened/created file
            - `mode`: the opening mode of the file
        """

        item = mode + u'#@#' + filepath
        recent_files = self.config.recent_files
        # Updates the list of recently open files. Most recent goes first.
        if not recent_files.contains(item):
            recent_files.insert(0, item)
        else:
            recent_files.removeAt(recent_files.indexOf(item))
            recent_files.insert(0, item)
        while recent_files.count() > self.number_of_recent_files:
            recent_files.takeLast()


    def updateFSHistory(self, working_dir):
        """Update the navigation history of the file selector widget.

        :Parameter `working_dir`: the last visited directory
        """

        self.config.last_working_directory = working_dir
        if not self.file_selector_history.contains(working_dir):
            self.file_selector_history.append(working_dir)
        else:
            self.file_selector_history.removeAll(working_dir)
            self.file_selector_history.append(working_dir)


    def checkFileExtension(self, filepath):
        """
        Check the filename extension of a given file.

        If the filename has no extension this method adds .h5
        extension to it. This is useful when a file is being created or
        saved.

        :Parameter filepath: the full path of the file (a QString)

        :Returns: the filepath with the proper extension (a Python string)
        """

        if not re.search('\.(.+)$', os.path.basename(filepath)):
            ext = '.h5'
            filepath = filepath + ext
        return filepath


    def fileNew(self):
        """Create a new file."""

        # Launch the file selector
        fs_args = {'accept_mode': QtGui.QFileDialog.AcceptOpen, 
            'file_mode': QtGui.QFileDialog.AnyFile, 
            'history': self.file_selector_history, 
            'label': trs('Create', 'Accept button text for QFileDialog')}
        filepath, working_dir = vitables.utils.getFilepath(
            self.gui, 
            trs('Creating a new file...', 
                'Caption of the File New... dialog'), 
            dfilter=trs("""HDF5 Files (*.h5 *.hd5 *.hdf5);;"""
                """All Files (*)""", 'Filter for the Open New dialog'), 
            settings=fs_args)

        if not filepath:
            # The user has canceled the dialog
            return

        # Update the history of the file selector widget
        self.updateFSHistory(working_dir)

        # Check the file extension
        filepath = self.checkFileExtension(filepath)

        # Check the returned path
        if os.path.exists(filepath):
            print trs(
                """\nWarning: """
                """new file creation failed because file already exists.""",
                'A file creation error')
            return

        # Create the pytables file and close it.
        db_doc = self.gui.dbs_tree_model.createDBDoc(filepath)
        if db_doc:
            # The write mode must be replaced by append mode or the file
            # will be created from scratch in the next ViTables session
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
        fs_args = {'accept_mode': QtGui.QFileDialog.AcceptSave, 
            'file_mode': QtGui.QFileDialog.AnyFile, 
            'history': self.file_selector_history, 
            'label': trs('Create', 'Accept button text for QFileDialog')}
        trier_filepath, working_dir = vitables.utils.getFilepath(
            self.gui, 
            trs('Copying a file...', 
                      'Caption of the File Save as... dialog'), 
            dfilter = trs("""HDF5 Files (*.h5 *.hd5 *.hdf5);;"""
                """All Files (*)""", 'Filter for the Save As... dialog'), 
            filepath=initial_filepath, 
            settings=fs_args)

        if not trier_filepath:  # The user has canceled the dialog
            return

        # Update the history of the file selector widget
        self.updateFSHistory(working_dir)

        trier_filepath = self.checkFileExtension(trier_filepath)

        #
        # Check if the chosen name is valid
        #

        info = [trs('File Save as: file already exists', 
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
                info[1] = trs("""Target directory: %s\n\nThe Query """
                                """results database cannot be overwritten.""", 
                                'Overwrite file dialog label') % trier_dirname
                pattern = \
                    "(^%s$)|[a-zA-Z_]+[0-9a-zA-Z_]*(?:\.[0-9a-zA-Z_]+)?$" \
                    % trier_filename
            elif is_initial_filepath:
                info[1] = trs("""Target directory: %s\n\nThe file """
                                """being saved cannot overwrite itself.""", 
                                'Overwrite file dialog label') % trier_dirname
                pattern = \
                    "(^%s$)|[a-zA-Z_]+[0-9a-zA-Z_]*(?:\.[0-9a-zA-Z_]+)?$" \
                    % trier_filename
            elif filename_in_sibling:
                info[1] = trs("""Target directory: %s\n\nFile name """
                    """'%s' already in use in that directory.\n""", 
                    'Overwrite file dialog label') % (trier_dirname, 
                    trier_filename)
                pattern = "[a-zA-Z_]+[0-9a-zA-Z_]*(?:\.[0-9a-zA-Z_]+)?$"

            dialog = renameDlg.RenameDlg(trier_filename, pattern, info)
            if dialog.exec_():
                trier_filename = dialog.action['new_name']
                trier_filepath = os.path.join(trier_dirname, trier_filename)
                trier_filepath = \
                    unicode(QtCore.QDir.fromNativeSeparators(trier_filepath))
                overwrite = dialog.action['overwrite']
                # Update the error conditions
                is_initial_filepath = trier_filepath == initial_filepath
                is_tmp_filepath = \
                    trier_filepath == self.gui.dbs_tree_model.tmp_filepath
                filename_in_sibling = trier_filename in sibling
                del dialog
                if (overwrite == True) and (not is_initial_filepath) and \
                    (not is_tmp_filepath):
                    break
            else:
                del dialog
                return

        filepath = self.checkFileExtension(trier_filepath)

        # If an open file is overwritten then close it
        if overwrite and self.gui.dbs_tree_model.getDBDoc(filepath):
            for row, child in enumerate(self.gui.dbs_tree_model.root.children):
                if child.filepath == filepath:
                    self.fileClose(self.gui.dbs_tree_model.index(row, 0, 
                                                        QtCore.QModelIndex()))
            # The current index could have changed when overwriting
            # so we update it
            for row in range(0, 
                self.gui.dbs_tree_model.rowCount(QtCore.QModelIndex())):
                index = QtCore.QModelIndex().child(row, 0)
                node = self.gui.dbs_tree_model.nodeFromIndex(index)
                if node.filepath == initial_filepath:
                    current_index = index
            self.gui.dbs_tree_view.setCurrentIndex(current_index)

        # Make a copy of the selected file
        try:
            QtGui.qApp.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            dbdoc = self.gui.dbs_tree_model.getDBDoc(initial_filepath)
            dbdoc.copyFile(filepath)
        finally:
            QtGui.qApp.restoreOverrideCursor()

        # Close the copied file (which is not necessarely selected in
        # the tree view because closing an overwritten file can change
        # the selected item) and open the new copy in read-write mode.
        # The position in the tree is kept
        for row, child in enumerate(self.gui.dbs_tree_model.root.children):
            if child.filepath == initial_filepath:
                self.fileClose(self.gui.dbs_tree_model.index(row, 0, 
                                                        QtCore.QModelIndex()))
                self.fileOpen(filepath, 'a', row) 


    def fileOpenRO(self, filepath=None):
        """
        Open a file that contains a ``PyTables`` database in read-only mode.

        :Parameters filepath: the full path of the file to be open
        """
        self.fileOpen(filepath, mode='r')


    def openRecentFile(self):
        """
        Opens the file whose path appears in the activated menu item text.
        """

        action = self.sender()
        item = action.data().toString()
        (mode, filepath) = unicode(item).split('#@#')
        self.fileOpen(filepath, mode)


    def clearRecentFiles(self):
        """
        Clear the list of recently opened files and delete the corresponding
        historical file.
        """

        self.config.recent_files.clear()


    def fileOpen(self, filepath=None, mode='a', position=0):
        """
        Open a file that contains a ``PyTables`` database.

        If this method is invoqued via ``File -> Open`` then no filepath
        is passed and a dialog is raised. When the method is invoqued
        via slotRecentSubmenuActivated or fileSaveAs methods then
        filepath is passed and the dialog is not raised.

        :Parameters:

        - `filepath`: the full path of the file to be open
        - `mode`: the file opening mode. It can be read-write or read-only
        - `position`: position in the tree view of the new file
        """

        if not filepath:
            # Launch the file selector
            fs_args = {'accept_mode': QtGui.QFileDialog.AcceptOpen, 
                'file_mode': QtGui.QFileDialog.ExistingFile, 
                'history': self.file_selector_history, 
                'label': trs('Open', 'Accept text for QFileDialog')}
            filepath, working_dir = vitables.utils.getFilepath(\
                self.gui, 
                trs('Select a file for opening', 
                'Caption of the File Open... dialog'), 
                dfilter = trs("""HDF5 Files (*.h5 *.hd5 *.hdf5);;"""
                    """All Files (*)""", 'Filter for the Open New dialog'), 
                settings=fs_args)

            if not filepath:
                # The user has canceled the dialog
                return

            # Update the history of the file selector widget
            self.updateFSHistory(working_dir)

        else:
            # Make sure the path contains no backslashes
            filepath = unicode(QtCore.QDir.fromNativeSeparators(filepath))

        # Open the database and select it in the tree view
        is_open = self.gui.dbs_tree_model.openDBDoc(filepath, mode, position)
        if is_open:
            self.gui.dbs_tree_model.getDBDoc(filepath)
            self.gui.dbs_tree_view.setCurrentIndex(\
                self.gui.dbs_tree_model.index(\
                position, 0, QtCore.QModelIndex()))
            self.updateRecentFiles(filepath, mode)


    def fileClose(self, current=False):
        """
        Close a file.

        First of all this method finds out which database it has to close.
        Afterwards all views belonging to that database are closed, then
        the object tree is removed from the QListView and, finally, the
        database is closed.

        current: the index of a node living in the file being closed
        """

        if current is False:
            current = self.gui.dbs_tree_view.currentIndex()
        filepath = self.gui.dbs_tree_model.nodeFromIndex(current).filepath

        # If some leaf of this database has an open view then close it
        for window in self.gui.workspace.subWindowList():
            if window.dbt_leaf.filepath == filepath:
                window.close()

        # The tree model closes the file and delete its root item
        # from the tree view
        dbdoc = self.gui.dbs_tree_model.getDBDoc(filepath)
        if dbdoc.hidden_group is not None:
            dbdoc.h5file.removeNode(dbdoc.hidden_group, recursive=True)
        self.gui.dbs_tree_model.closeDBDoc(filepath)


    def fileCloseAll(self):
        """Close every file opened by user."""

        # The list of top level items to be removed.
        # The temporary database should be closed at quit time only
        open_files = len(self.gui.dbs_tree_model.root.children) - 1
        rows_range = range(0, open_files)
        # Reversing is a must because, if we start from 0, row positions
        # change as we delete rows
        rows_range.reverse()
        for row in rows_range:
            index = self.gui.dbs_tree_model.index(row, 0, QtCore.QModelIndex())
            self.fileClose(index)


    def fileExit(self):
        """
        Safely closes the application.

        Save current configuration on disk, closes opened files and exits.
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


    def nodeOpen(self, current=False):
        """
        Opens a leaf node for viewing.

        :Parameter current: the model index of the item to be opened
        """

        if current is False:
            # Open the node currently selected in the tree of databases
            index = self.gui.dbs_tree_view.currentIndex()
        else:
            # When restoring the previous session explicit indexes are passed
            index = current
        dbs_tree_leaf = self.gui.dbs_tree_model.nodeFromIndex(index)
        leaf = dbs_tree_leaf.node # A PyTables node

        # tables.UnImplemented datasets cannot be read so are not opened
        if isinstance(leaf, tables.UnImplemented):
            QtGui.QMessageBox.information(self, 
                trs('About UnImplemented nodes', 'A dialog caption'), 
                trs(
                """Actual data for this node are not accesible.<br> """
                """The combination of datatypes and/or dataspaces in this """
                """node is not yet supported by PyTables.<br>"""
                """If you want to see this kind of dataset implemented in """
                """PyTables, please, contact the developers.""",
                'Text of the Unimplemented node dialog'))
            return

        # The buffer tied to this node in order to optimize the read access
        leaf_buffer = rbuffer.Buffer(leaf)

        # Leaves that cannot be read are not opened
        if not leaf_buffer.isDataSourceReadable():
            return

        # Create a view and announce it.
        # Announcing is potentially helpful for plugins in charge of
        # datasets customisations (for instance, additional formatting)
        subwindow = dataSheet.DataSheet(index)
        subwindow.show()
        self.leaf_model_created.emit(subwindow)


    def nodeClose(self, current=False):
        """
        Closes the view of the selected node.

        The method is called by activating ``Node --> Close`` (what passes
        no argument) or programatically by the ``VTApp.fileClose()``
        method (what does pass argument).
        If the target is an open leaf this method closes its view, delete
        its model and updates the controller tracking system.
        If the target node is a root group the method looks for opened
        children and closes them as described above.

        :Parameter current: the tree view item to be closed
        """

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
        dialog = inputNodeName.InputNodeName(\
            trs('Creating a new group', 'A dialog caption'), 
            trs('Source file: %s\nParent group: %s\n\n ', 
                'A dialog label') % (parent.filepath, parent.nodepath), 
            trs('Create', 'A button label'))
        if dialog.exec_():
            suggested_nodename = dialog.node_name
            del dialog
        else:
            del dialog
            return

        #
        # Check if the entered nodename is already in use
        #
        sibling = getattr(parent.node, '_v_children').keys()
        pattern = "[a-zA-Z_]+[0-9a-zA-Z_ ]*"
        info = [trs('Creating a new group: name already in use', 
                'A dialog caption'), 
                trs("""Source file: %s\nParent group: %s\n\nThere is """
                          """already a node named '%s' in that parent group"""
                          """.\n""", 'A dialog label') % \
                    (parent.filepath, parent.nodepath, suggested_nodename)]
        nodename, overwrite = vitables.utils.getFinalName(suggested_nodename, 
            sibling, pattern, info)
        if nodename is None:
            return

        # If the creation overwrites a group with attached views then these
        # views are closed before the renaming is done
        if overwrite:
            nodepath = tables.path.joinPath(parent.nodepath, nodename)
            self.gui.closeChildrenViews(nodepath, parent.filepath)

        self.gui.dbs_tree_model.createGroup(current, nodename, overwrite)


    def nodeRename(self):
        """
        Rename the selected node.

        - ask for the node name
        - check the node name. If it is already in use ask what to<br>
          do (possibilities are rename, overwrite and cancel creation)
        - rename the node
        """

        index = self.gui.dbs_tree_view.currentIndex()
        child = self.gui.dbs_tree_model.nodeFromIndex(index)
        parent = child.parent

        # Get the new nodename
        dialog = inputNodeName.InputNodeName(\
            trs('Renaming a node', 'A dialog caption'),
            trs('Source file: %s\nParent group: %s\n\n', 
                    'A dialog label') % (parent.filepath, parent.nodepath), 
            trs('Rename', 'A button label'))
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
        pattern = """(^%s$)|""" \
            """(^[a-zA-Z_]+[0-9a-zA-Z_ ]*)""" % child.name
        info = [trs('Renaming a node: name already in use', 
                'A dialog caption'), 
                trs("""Source file: %s\nParent group: %s\n\nThere is """
                          """already a node named '%s' in that parent """
                          """group.\n""", 'A dialog label') % \
                    (parent.filepath, parent.nodepath, suggested_nodename)]
        nodename, overwrite = vitables.utils.getFinalName(suggested_nodename, 
            sibling, pattern, info)
        if nodename is None:
            return

        # If the renaming overwrites a node with attached views then these
        # views are closed before the renaming is done
        if overwrite:
            nodepath = tables.path.joinPath(parent.nodepath, nodename)
            self.gui.closeChildrenViews(nodepath, child.filepath)

        # Rename the node
        self.gui.dbs_tree_model.renameNode(index, nodename, overwrite)

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
            leaf = dbs_tree_node.node # A PyTables node
            leaf_buffer = rbuffer.Buffer(leaf)
            if not leaf_buffer.isDataSourceReadable():
                QtGui.QMessageBox.information(self, 
                    trs('About unreadable datasets', 'Dialog caption'), 
                    trs(
                    """Sorry, actual data for this node are not accesible."""
                    """<br>The node will not be copied.""", 
                    'Text of the Unimplemented node dialog'))
                return

        # Copy the node
        self.gui.dbs_tree_model.copyNode(current)


    def nodePaste(self):
        """
        Paste the currently copied/cut node under the selected node.
        """

        current = self.gui.dbs_tree_view.currentIndex()
        parent = self.gui.dbs_tree_model.nodeFromIndex(current)

        copied_node_info = self.gui.dbs_tree_model.copied_node_info
        if copied_node_info == {}:
            return

        src_node = copied_node_info['node']
        src_filepath = src_node.filepath
        src_nodepath = src_node.nodepath
        if src_nodepath == '/':
            nodename = 'root_group_of_%s' \
                        % os.path.basename(src_filepath)
        else:
            nodename = src_node.name

        dbdoc = self.gui.dbs_tree_model.getDBDoc(\
            copied_node_info['initial_filepath'])
        if not dbdoc:
            # The database where the copied/cut node lived has been closed
            return
        if src_filepath != copied_node_info['initial_filepath']:
            # The copied/cut node doesn't exist. It has been moved to
            # other file
            return

        # Check if the copied node still exists in the tree of databases
        if copied_node_info['is_copied']:
            if src_nodepath != copied_node_info['initial_nodepath']:
                # The copied node doesn't exist. It has been moved somewhere
                return
            if not dbdoc.h5file.__contains__(src_nodepath):
                return

            # Check if pasting is allowed. It is not when the node has been
            # copied (pasting cut nodes has no restrictions) and
            # - source and target are the same node
            # - target is the source's parent
            if (src_filepath == parent.filepath):
                if (src_nodepath == parent.nodepath) or \
                   (parent.nodepath == src_node.parent.nodepath):
                    return

        #
        # Check if the nodename is already in use
        #
        sibling = getattr(parent.node, '_v_children').keys()
        # Nodename pattern
        pattern = "[a-zA-Z_]+[0-9a-zA-Z_ ]*"
        # Bad nodename conditions
        info = [trs('Node paste: nodename already exists', 
                'A dialog caption'), 
                trs("""Source file: %s\nCopied node: %s\n"""
                    """Destination file: %s\nParent group: %s\n\n"""
                    """Node name '%s' already in use in that group.\n""", 
                    'A dialog label') % \
                    (src_filepath, src_nodepath,
                    parent.filepath, parent.nodepath, nodename), 
                trs('Paste', 'A button label')]
        # Validate the nodename
        nodename, overwrite = vitables.utils.getFinalName(nodename, sibling, 
            pattern, info)
        if nodename is None:
            return

        # If the pasting overwrites a node with attached views then these
        # views are closed before the pasting is done
        if overwrite:
            nodepath = tables.path.joinPath(parent.nodepath, nodename)
            self.gui.closeChildrenViews(nodepath, parent.filepath)

        # Paste the node
        self.gui.dbs_tree_model.pasteNode(current, nodename, overwrite)


    def nodeDelete(self, current=False, force=None):
        """
        Delete a given node.

        :Parameters;

            - `force`: ask/do not ask for confirmation before deletion
        """

        if current is False:
            current = self.gui.dbs_tree_view.currentIndex()
        node = self.gui.dbs_tree_model.nodeFromIndex(current)

        # Confirm deletion dialog
        if not force:
            title = trs('Node deletion', 'Caption of the node deletion dialog')
            text = trs("""\nYou are about to delete the node:\n%s\n""", 
                'Ask for confirmation') % node.nodepath
            itext = ''
            dtext = ''
            buttons = {\
                'Delete': \
                    (trs('Delete', 'Button text'), QtGui.QMessageBox.YesRole), 
                'Cancel': \
                    (trs('Cancel', 'Button text'), QtGui.QMessageBox.NoRole), 
                }

            # Ask for confirmation
            answer = \
                vitables.utils.questionBox(title, text, itext, dtext, buttons)
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

        # Synchronise the workspace with the tree of databases pane i.e.
        # ensure that the new current node (if any) gets selected
        select_model = self.gui.dbs_tree_view.selectionModel()
        new_current = self.gui.dbs_tree_view.currentIndex()
        select_model.select(new_current, QtGui.QItemSelectionModel.Select)


    def nodeProperties(self):
        """
        Display the properties dialog for the currently selected node.

        The method is called by activating Node --> Properties.
        """

        current = self.gui.dbs_tree_view.currentIndex()
        node = self.gui.dbs_tree_model.nodeFromIndex(current)
        info = nodeInfo.NodeInfo(node)
        nodePropDlg.NodePropDlg(info)


    def newQuery(self):
        """Slot for querying tables."""
        self.queries_mgr.newQuery()


    def deleteAllQueries(self):
        """Slot for emptying the Query results node."""
        self.queries_mgr.deleteAllQueries()


    def settingsPreferences(self):
        """
        Launch the Preferences dialog.

        Clicking the ``OK`` button applies the configuration set in the
        Preferences dialog.
        """

        prefs =  preferences.Preferences()
        try:
            if prefs.exec_() == QtGui.QDialog.Accepted:
                self.config.loadConfiguration(prefs.new_prefs)
        finally:
            del prefs


    def windowClose(self):
        """Close the window currently active in the workspace."""
        self.gui.workspace.activeSubWindow().close()


    def windowCloseAll(self):
        """Close all open windows."""

        for window in self.gui.workspace.subWindowList():
            window.close()


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
        Open the documentation browser

        Help --> UsersGuide
        """

        self.doc_browser = helpBrowser.HelpBrowser()


    def helpAbout(self):
        """
        Show a tabbed dialog with the application About and License info.

        Help --> About
        """

        # Text to be displayed
        about_text = trs(
            """<qt>
            <h3>ViTables %s</h3>
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
            </qt>""",
            'Text of the About ViTables dialog')  % vtconfig.getVersion()
        thanks_text = trs(
            """<qt>
            Dmitrijs Ledkovs for contributing the new and greatly enhanced
            build system and for making Debian packages.<p>
            Oxygen team for a wonderful icons set.<p>
            All the people who reported bugs and made suggestions.
            </qt>""",
            'Text of the About ViTables dialog (Thanks to page)')
        license_text = vitables.utils.getLicense()

        # Construct the dialog
        about_dlg = QtGui.QDialog(self.gui)
        about_dlg.setWindowTitle(trs('About ViTables %s',
            'Caption of the About ViTables dialog') % vtconfig.getVersion())
        layout = QtGui.QVBoxLayout(about_dlg)
        tab_widget = QtGui.QTabWidget(about_dlg)
        buttons_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        layout.addWidget(tab_widget)
        layout.addWidget(buttons_box)

        buttons_box.accepted.connect(about_dlg.accept)

        # Make About page
        content = [about_text, thanks_text, license_text]
        tabs = [trs('&About',
            'Title of the first tab of the About dialog'), 
            trs('&Thanks To',
            'Title of the second tab of the About dialog'), 
            trs('&License',
            'Title of the third tab of the About dialog')]

        for index in range(0, 3):
            widget = self.makePage(content[index])
            tab_widget.addTab(widget, tabs[index])


        # Show the dialog
        about_dlg.exec_()


    def makePage(self, content):
        """Create a page for the About ViTables dialog.

        :Parameter content: the text displayed on the page
        """

        widget = QtGui.QWidget()
        widget.setLayout(QtGui.QVBoxLayout())
        text_edit = QtGui.QTextEdit(widget)
        text_edit.setReadOnly(1)
        text_edit.setAcceptRichText(True)
        text_edit.setText(content)
        widget.layout().addWidget(text_edit)

        return widget


    def helpAboutQt(self):
        """
        Shows a message box with the Qt About info.

        Help --> About Qt
        """

        QtGui.QMessageBox.aboutQt(self.gui, trs('About Qt',
            'Caption of the About Qt dialog'))


    def helpVersions(self):
        """
        Message box with info about versions of libraries used by
        ViTables.

        Help --> Show Versions
        """

        # The libraries versions dictionary
        libs_versions = {
            'title': trs('Version Numbers',
                'Caption of the Versions dialog'),
            'Python': reduce(lambda x,y: '.'.join([unicode(x), unicode(y)]), 
                sys.version_info[:3]),
            'PyTables': tables.__version__ ,
            'NumPy': tables.numpy.__version__,
            'Qt': QtCore.qVersion(),
            'PyQt': QtCore.PYQT_VERSION_STR,
            'ViTables': vtconfig.getVersion()
        }

        # Add new items to the dictionary
        libraries = ('HDF5', 'Zlib', 'LZO', 'BZIP2')
        for lib in libraries:
            lversion = tables.whichLibVersion(lib.lower())
            if lversion:
                libs_versions[lib] = lversion[1]
            else:
                libs_versions[lib] = trs('not available',
                    'Part of the library not found text')

        # Construct the dialog
        versions_dlg = QtGui.QDialog(self.gui)
        versions_dlg.setWindowTitle(trs('Version Numbers', 
                                             'Caption of the Versions dialog'))
        layout = QtGui.QVBoxLayout(versions_dlg)
        versions_edit = QtGui.QTextEdit(versions_dlg)
        buttons_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        layout.addWidget(versions_edit)
        layout.addWidget(buttons_box)

        buttons_box.accepted.connect(versions_dlg.accept)

        versions_edit.setReadOnly(1)
        versions_edit.setText(\
            """
            <qt>
            <h3>%(title)s</h3><br>
            <table>
            <tr><td><b>Python</b></td><td>%(Python)s</td></tr>
            <tr><td><b>PyTables</b></td><td>%(PyTables)s</td></tr>
            <tr><td><b>NumPy</b></td><td>%(NumPy)s</td></tr>
            <tr><td><b>HDF5</b></td><td>%(HDF5)s</td></tr>
            <tr><td><b>Zlib</b></td><td>%(Zlib)s</td></tr>
            <tr><td><b>LZO</b></td><td>%(LZO)s</td></tr>
            <tr><td><b>BZIP2</b></td><td>%(BZIP2)s</td></tr>
            <tr><td><b>Qt</b></td><td>%(Qt)s</td></tr>
            <tr><td><b>PyQt</b></td><td>%(PyQt)s</td></tr>
            <tr><td><b>ViTables</b></td><td>%(ViTables)s</td></tr>
            </table>
            </qt>""" % libs_versions)

        # Show the dialog
        versions_dlg.exec_()
