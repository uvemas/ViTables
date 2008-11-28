# -*- coding: utf-8 -*-

########################################################################
#
#       Copyright (C) 2005, 2006 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008 Vicent Mas. All rights reserved
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
#
#       $Source$
#       $Id: dbManager.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the DBManager class.

Classes:

* DBManager(qt.QObject)

Methods:

* __init__(self, gui)
* __tr(self, source, comment=None)
* checkOpening(self, filepath)
* openDB(self, filepath, mode, tmp_db=False)
* closeDB(self, filepath)
* getDB(self, filepath)
* getDBView(self, filepath)
* dbList(self)
* getCutNodes(self)
* clearHiddenGroup(self)
* createTempDB(self)
* createFile(self, filepath, tmp_db=False)
* copyFile(self, src_filepath, dst_filepath)
* createGroup(self, filepath, where, final_name)
* cut(self, dbdoc, where, name)
* paste(self, src_dbdoc, src_nodepath, target_dbdoc, parentpath, final_name)
* dropNode(self, src_dbdoc, src_nodepath, target_dbdoc, target_parentpath, final_name)
* rename(self, dbdoc, where, final_name, initial_name)
* delete(self, dbdoc, where, name, is_visible=True)

Functions:

* getFinalName(editing, target_data, src_data)
* getInitialName(header, current, label, caption, is_file=False)

Misc variables:

- __docformat__

"""
__docformat__ = 'restructuredtext'

import tempfile
import os

import tables
import qt

import vitables.utils
from vitables.vtWidgets import vtInputBox
from vitables.vtWidgets import renameDlg
from vitables.h5db import dbDoc
from vitables.h5db import dbView

def getFinalName(editing, target_data, src_data):
    """
    Get a new name if the candidate name is already in use.

    This method is used to detect naming problems when editing action
    is one of:

    - a group is being created
    - a node is being pasted/dropped
    - a node is being renamed
    - a file save as

    If the name being set is already being used by a sibling
    file/node then user has to decide what to do: try a new name, overwrite
    the existing file/node or cancel the operation.

    The contents of `target_data` and `src_data` depend on the editing action:
    
    :create_group:

    - `target_data`: ``[filepath, parentpath, nodename, parent_group]``
    - `src_data`: ``[]``

    :paste_node and move_node:

    - `target_data`: ``[filepath, parentpath, nodename, parent_group]``
    - `src_data`: ``[filepath, nodepath]``

    :rename_node:

    - `target_data`: ``[filepath, parentpath, nodename, parent_group]``
    - `src_data`: ``[initial_name]``

    :save_as:

    - `target_data`: ``[dirname, filename]``
    - `src_data`: ``[initial_name, tmpDBpath]``

    :Parameters:

    - `editing`: the editing action being done
    - `target_data`: useful data regarding the file/node destination
    - `src_data`: useful data regarding the file/node origin
    """

    if editing == "save_as":
        # The file (potentially troubled) new name
        name = target_data.pop()
        # The list of file names that can trouble with the new filename
        # Note that we have appended the temporary database
        trouble_names = os.listdir(target_data[0]) + [src_data[-1]]

    else:
        # The destination group
        parent = target_data.pop()
        # The node (potentially troubled) new name
        name = target_data.pop()
        # The list of node names that can trouble with the node newname
        # We append '/' because there can only be one root node
        trouble_names = parent._v_children.keys() + ['/']

    # Check if another node is being overwritten
    overwrite = False
    while name in trouble_names:
        new_name = name
        # The dialog info depends on the editing action being executed
        data = src_data + target_data + [new_name]
        ask = renameDlg.RenameDlg(editing, data)
        ask.exec_loop()
        action = ask.action.copy()
        name = action['new_nodename']
        overwrite = action['overwrite']
        # If the user clicks Overwrite or Cancel then quit the loop
        if overwrite or not name:
            break
    return name,  overwrite


def getInitialName(header, current, label, caption, is_file=False):
    """
    A dialog for entering a candidate nodename.

    This method is used to enter new group names, rename nodes, 
    paste/drop nodes and save a file as a different one.

    :Parameters:

    - `header`: an explanatory text
    - `current`: the current name of the item
    - `label`: a label for the input name dialog
    - `caption`: the caption of the input name dialog
    """

    get_name_dlg = vtInputBox.VTInputBox(header, current, label, caption,
        is_file)
    try:
        get_name_dlg.exec_loop()
        # OK clicked
        if get_name_dlg.result() == qt.QDialog.Accepted:
            initial_name = get_name_dlg.newValue
        # Cancel clicked
        else:
            initial_name = ''
    finally:
        del get_name_dlg
    return initial_name


class DBManager(qt.QObject):
    """
    Manages the opening/closing of databases.

    As the other managers, this one is created at application init
    time.
    This class is a controller of open databases (including those
    store filtered tables).
    In particular it is intended to:

    - create models (`DBDoc` instances)
    - bind every created model to a unique view
    - destroy models when its binded view is destroyed
    - keep track of existing models
    - handle user input related with databases (reading/editing operations)

    Views are root nodes displayed in the application tree viewer.

    Aside of open databases and their object tree representation this
    class manages also the temporary database (creation/deletion and
    updates).
    Query results are stored in a temporary file that is destroyed when
    the application quits. The results are shown in the tree pane as
    children of the `Query results` item.
    """


    def __init__(self, gui):
        """
        Initialize the tracking system and create the temporary database.

        :Parameter gui: the application main window
        """

        qt.QObject.__init__(self)

        # The application main widget
        self.vtgui = gui

        # Dictionary used for tracking opened databases.
        # keys are full path of open databases
        # values are pairs (DBDoc, DBView)
        self._openDB = {}

        # Create the temporary database that will contain filtered tables
        # and (under a idden group) cut nodes
        self.tmp_filepath = ''
        self.hidden_where = '/_p_cutNode'
        self.createTempDB()
        self.tmp_dbdoc = self.getDB(self.tmp_filepath)


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('DBManager', source, comment).latin1()

    #
    # Reading databases
    #

    def checkOpening(self, filepath):
        """
        Check if a database can be open.
        
        :Parameter filepath: the full path of the file
        """

        try:
            # Check if file doesn't exist
            if os.path.isdir(filepath):
                error = self.__tr('Openning cancelled: %s is a folder.',
                    'A logger error message') % filepath
                raise ValueError, error
            elif not os.path.isfile(filepath):
                error = self.__tr('Opening failed: file %s cannot be found.',
                    'A logger error message') % filepath
                raise ValueError, error

            # Check if file is already open.
            elif self._openDB.has_key(filepath):
                error = self.__tr('Opening cancelled: file %s already open.',
                    'A logger error message') % filepath
                raise ValueError, error

            # Check the file format
            else:
                try:
                    tables.isHDF5File(filepath)
                except:
                    error = \
                        self.__tr('Opening failed: %s has not HDF5 format.', 
                        'A logger error message') % filepath
                    raise ValueError, error
        except ValueError:
            print error
            return False
        else:
            return True


    def openDB(self, filepath, mode, tmp_db=False):
        """
        Open an existing hdf5 file.

        The opened database is binded to a pair `(DBDoc, DBView)`.

        :Parameters:

        - `filepath`: full path of the database file we wish to open.
        - `mode`: the opening mode of the database file. It can be 'r'ead-only
            'w'rite or 'a'ppend
        - `tmp_db`: indicates if the file being opened is a temporary database

        :Returns: a `(dbDoc, dbView)` pair
        """

        if isinstance(filepath, qt.QString):
            filepath = filepath.latin1()

        if self.checkOpening(filepath):


            opendb_ok = False
            # Creates a model
            dbdoc = dbDoc.DBDoc(filepath, mode)
            # One more check
            if dbdoc.h5_file:
                # Attach a view to the model
                dbview = dbView.DBView(dbdoc, self.vtgui, tmp_db)
                dbdoc.dbview = dbview
                # Keeps track of open models and views
                self._openDB[filepath] = (dbdoc, dbview)
                # Once the database has been tracked the tree view selection
                # status is updated, which triggers the VTApp.slotUpdateActions
                # method and its tied methods
                self.vtgui.otLV.setCurrentItem(dbview.root_item)
                opendb_ok = True

            return opendb_ok


    def closeDB(self, filepath):
        """
        Close the DB file and update the tracking of open DBs.

        The temporary database cannot be closed by the user. It is
        automatically closed when the application exits.
        :Warning:
          Note that order matters in the closing sequence because there
          is a race condition.
        
        The tracking dictionary must be updated before the tree view
        gets updated. If not, the currentChanged SIGNAL could be emitted
        before the tracking system was updated and the method
        ``VTApp.updateFileActions`` would lead to a wrong update of the
        `fileCloseAll` `QAction` (for instance when there is only one
        open file).

        :Parameters:

        - `filepath`: the full path of the file being closed
        - `root`: the tree view item corresponding to the root node of the
            file being closed
        """

        if isinstance(filepath, qt.QString):
            filepath = filepath.latin1()

        # The view and model being closed
        view = self.getDBView(filepath)
        dbdoc = self.getDB(filepath)

        # First updates the tracking dictionary
        del self._openDB[filepath]
        if filepath == self.tmp_filepath:
            self.tmp_dbdoc = None

        # Then update the tree view
        root = view.getRootItem()
        self.vtgui.otLV.takeItem(root)
        del root
        self.vtgui.otLV.repaintContents()

        # Finally close the HDF5 file
        dbdoc.closeH5File()


    def getDB(self, filepath):
        """
        Get the database document mapped to the given file.

        This is a getter method that allows to external classes to inspect
        the tracking dictionary.

        :Parameter filepath: the full path of the database file

        :Returns: the DBDoc instance mapped to the given file
        """

        if isinstance(filepath, qt.QString):
            filepath = filepath.latin1()
        if self._openDB.has_key(filepath):
            return self._openDB[filepath][0]
        else:
            return None


    def getDBView(self, filepath):
        """
        Get the database view mapped to the given file.

        This is a getter method that allows to external classes to inspect
        the tracking dictionary.

        :Parameter filepath: the full path of the database file

        :Returns: the dbView instance mapped to the given file
        """

        if isinstance(filepath, qt.QString):
            filepath = filepath.latin1()
        return self._openDB[filepath][1]


    def dbList(self):
        """
        The list of currently open files.

        This list is used to save the session state at quiting time.
        It doesn't include the file used by the temporary database.
        The returned list has the format ``[filepath1,  filepth2, ...]``

        :Returns: the list of currently open files
        """
        return [key for key in self._openDB.keys() if key != self.tmp_filepath]


    def getCutNodes(self):
        """
        Get the contents of the hidden group of the temporary database.

        Cut nodes are stored in a hidden group of the temporary database. At
        a given time at most one cut node is stored. This way a paste operation
        knows which node has to be pasted: it first look at the hidden group,
        if there is a node then it is pasted. If not then the clipboard content
        is pasted.

        :Returns: the list of cut nodes
        """

        # The hidden group of the temporary database
        hidden_group = self.tmp_dbdoc.getNode(self.hidden_where)
        # The list of cut nodes paths
        return hidden_group._v_children.keys()


    def clearHiddenGroup(self):
        """
        Clear the hidden group of the temporary database.

        Clear the contents of the hidden group before a new cut/copy is
        done. It means that at most one node will live in the hidden group
        at a given time.
        """

        # The list of cut nodes paths
        cut_nodes = self.getCutNodes()
        for nodename in cut_nodes:
            cut_nodename = os.path.basename(nodename)
            self.tmp_dbdoc.delete(self.hidden_where, cut_nodename, False)


    #
    # Editing databases
    #

    def createTempDB(self):
        """
        Create a temporary database where filtered tables will be stored.

        The database will have a hidden group where cut nodes can be
        stored until they are pasted somewhere else.
        """

        print self.__tr('Creating the Query results file...',
            'A logger info message')
        (f_handler, self.tmp_filepath) = tempfile.mkstemp('.h5', 'FT_')
        os.close(f_handler)
        creation_ok = self.createFile(self.tmp_filepath, tmp_db=True)
        if not creation_ok:
            print self.__tr(
                """\nFile creation failed due to unknown reasons!\nPlease, """
                """have a look to the last error displayed in the """
                """logger. If you think it's a bug, please report it"""
                """ to developers.""",
                'A file creation error')
            return

        tmp_h5file = self.getDB(self.tmp_filepath).getH5File()
        try:
            tmp_h5file.createGroup('/', self.hidden_where[1:], 'Hide cut nodes')
            print self.__tr('OK!', 'Operation successful logger message')
        except:
            vitables.utils.formatExceptionInfo()


    def createFile(self, filepath, tmp_db=False):
        """
        Create a new file.

        :Parameter filepath: the full path of the file being created.
        """

        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))
        try:
            creation_ok = False
            # Make the creation in the object tree.
            # creation_ok will be True if the file is succesfully created
            # and False if not.
            try:
                mode = 'w'
                # Creates a model
                dbdoc = dbDoc.DBDoc(filepath, 'w')
                # One more check
                if dbdoc.h5_file:
                    # Attach a view to the model
                    dbview = dbView.DBView(dbdoc, self.vtgui, tmp_db)
                    dbdoc.dbview = dbview
                    # Keeps track of open models and views
                    self._openDB[filepath] = (dbdoc, dbview)
                    # Once the database has been tracked the tree view selection
                    # status is updated, which triggers the VTApp.slotUpdateActions
                    # method and its tied methods
                    self.vtgui.otLV.setCurrentItem(dbview.root_item)
                creation_ok = True
            except:
                vitables.utils.formatExceptionInfo()
        finally:
            qt.qApp.restoreOverrideCursor()
        return creation_ok


    def copyFile(self, src_filepath, dst_filepath):
        """
        Copy the contents of a file to another one.

        :Parameters:

        - `src_filepath`: the full path of the file being copied.
        - `dst_filepath`: the full path of the destination file.
        """

        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))
        try:
            dbdoc = self.getDB(src_filepath)
            dbdoc.copyFile(dst_filepath)
        finally:
            qt.qApp.restoreOverrideCursor()


    def createGroup(self, filepath, where, final_name):
        """
        Create a new group under the given location.

        :Parameters:

        - `filepath`: the full path of the database where the group will live
        - `where`: the path of the parent of the group being created
        - `final_name`: the wanted name for the group being created
        """

        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))
        try:
            dbdoc = self.getDB(filepath)
            dbdoc.createGroup(where, final_name)
        finally:
            qt.qApp.restoreOverrideCursor()


    def cut(self, dbdoc, where, name):
        """
        Cut the selected node.

        :Parameters:

        - `dbdoc`: the database where the node being cut lives
        - `where`: the path of the parent of the node being cut
        - `name`: the name of the node being cut
        """

        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))

        try:
            # Cleanup the hidden group where the cut node will be stored
            self.clearHiddenGroup()

            target_node = self.tmp_dbdoc.getNode(self.hidden_where)
            dbdoc.cut(where, name, target_node)
        finally:
            qt.qApp.restoreOverrideCursor()


    def paste(self, src_dbdoc, src_nodepath, target_dbdoc, parentpath,
        final_name):
        """
        Paste a copied/cut node under the selected group.

        :Parameters:

        - `src_dbdoc`: the database where the node being pasted lives
        - `src_nodepath`:
            the full path in the source database of the node being pasted
        - `target_dbdoc`: the database where the node being pasted will live
        - `parentpath`: the path of the target group
        - `final_name`: the wanted name for the node being pasted
        """

        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))

        try:
            # Paste the node
            src_dbdoc.copyNode(src_dbdoc, src_nodepath, target_dbdoc, parentpath,
                final_name)
        finally:
            qt.qApp.restoreOverrideCursor()
            return True


    def dropNode(self, src_dbdoc, src_nodepath, target_dbdoc, 
        target_parentpath, final_name):
        """
        Move a node to a different location.

        :Parameters:

        - `src_dbdoc`: the database where the node being dropped lives
        - `src_nodepath`: the full path in the source database of the
            node being dropped
        - `target_dbdoc`: the database where the node being dropped will
            live
        - `target_parentpath`: the path of the new parent group of the
            node being dropped
        - `final_name`: the wanted name for the node being dropped
        """

        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))
        try:
            # Drop the node
            src_dbdoc.move(src_nodepath, target_dbdoc, target_parentpath, 
                final_name)
        finally:
            qt.qApp.restoreOverrideCursor()


    def rename(self, dbdoc, where, final_name, initial_name):
        """
        Rename the selected node.

        :Parameters:

        - `dbdoc`: the database where the node being renamed lives
        - `where`: the path of the parent of the node being renamed
        - `initial_name`: the current name of the node being renamed
        - `final_name`: the wanted name for the node being renamed
        """

        # Get the tables.File instance and the selected node full path
        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))
        try:
            # Makes the rename in the object tree
            dbdoc.rename(where, final_name, initial_name)
        finally:
            qt.qApp.restoreOverrideCursor()


    def delete(self, dbdoc, where, name, is_visible=True):
        """
        Delete the selected node.

        :Parameters:

        - `dbdoc`: the database where the node being deleted lives
        - `where`: the path of the parent of the node being deleted
        - `name`: the name of the node being deleted
        """

        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))
        try:
            # Makes the deletion in the object tree
            dbdoc.delete(where, name, is_visible)
        finally:
            qt.qApp.restoreOverrideCursor()


