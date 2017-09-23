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
This module defines a model (in the `MVC` sense) representing the tree of
databases.

The model is populated using data structures defined in the
:mod:`vitables.h5db.rootgroupnode`, :mod:`vitables.h5db.groupnode` and
:mod:`vitables.h5db.leafnode` modules.
"""

__docformat__ = 'restructuredtext'

import tempfile
import os
import sys
import re
import logging

import tables

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.utils
from vitables.h5db import dbdoc
from vitables.h5db import rootgroupnode
from vitables.h5db import groupnode
from vitables.h5db import leafnode
from vitables.h5db import linknode
from vitables.h5db import tnode_editor
from vitables.h5db import tlink_editor

translate = QtWidgets.QApplication.translate

log = logging.getLogger(__name__)


def _get_node_tooltip(node):
    """Takes one of vitables nodes and return tooltip text.

    :Parameters node: a node from the tree model
    """

    tooltip_lines = []
    attrset = node.node._v_attrs
    if not hasattr(node.node, 'target'):
        if hasattr(attrset, 'TITLE') and bool(str(attrset.TITLE)):
            tooltip_lines.append(attrset.TITLE)
    tooltip_lines.append('{0}: {1}'.format(node.node_kind, node.name))
    tooltip_lines.extend(
        ['{0}: {1}'.format(name, str(getattr(attrset, name)))
         for name in attrset._v_attrnamesuser])
    return '\n'.join(tooltip_lines)


# Map qt display role onto a function that gets data from a node.
_ROLE_NODE_GET_FUNCTION_DICT = {
    QtCore.Qt.DisplayRole: lambda n: getattr(n, 'name'),
    QtCore.Qt.ToolTipRole: _get_node_tooltip,
    QtCore.Qt.StatusTipRole: lambda n: getattr(n, 'as_record'),
    QtCore.Qt.DecorationRole: lambda n: getattr(n, 'icon'),
    QtCore.Qt.UserRole: lambda n: getattr(n, 'filepath'),
    QtCore.Qt.UserRole + 1: lambda n: getattr(n, 'nodepath'),
    QtCore.Qt.UserRole + 2: lambda n: getattr(n, 'node_kind')
}


class DBsTreeModel(QtCore.QAbstractItemModel):
    """
    The tree of databases model.

    The data is read and written from and to data sources (i.e., HDF5/PyTables
    files) by the model.

    :Parameters vtapp: the VTAPP instance
    """

    def __init__(self, vtgui, vtapp):
        """Create the model.
        """

        # The underlying data structure used to populate the model
        self.root = rootgroupnode.RootGroupNode(self)

        super(DBsTreeModel, self).__init__(parent=None)
        self.setObjectName("dbs_tree_model")

        # The dictionary of open databases
        self.__openDBs = {}

        # Create the temporary database that will contain filtered tables
        self.tmp_filepath = ''
        self.tmp_dbdoc = self.__createTempDB()

        # The Cut/CopiedNodeInfo dictionary
        self.ccni = {}
        self.vtapp = vtapp
        self.vtgui = vtgui

        # Sets used to populate the model
        self.fdelta = frozenset([])
        self.gdelta = frozenset([])
        self.ldelta = frozenset([])
        self.links_delta = frozenset([])

        self.rowsAboutToBeRemoved.connect(self.closeViews)

    def mapDB(self, filepath, db_doc):
        """Maps a file path with a :meth:`dbdoc.DBDoc` instance.

        :Parameters:

        - `filepath`: the full path of an open database.
        - `db_doc`: a :meth:`dbdoc.DBDoc` instance.
        """
        self.__openDBs[filepath] = db_doc

    def removeMappedDB(self, filepath):
        """Remove a :meth:`dbdoc.DBDoc` instance from the tracking dict.

        :Parameter filepath: the full path of the database being untracked
        """
        del self.__openDBs[filepath]

    def getDBDoc(self, filepath):
        """Returns the DBDoc instance tied to a given file path.

        :Parameter filepath: the full path of an open database.
        """
        if filepath in self.__openDBs:
            return self.__openDBs[filepath]
        else:
            return None

    def getDBList(self):
        """Returns the list of paths of files currently open.

        The temporary database is not included in the list.
        """

        filepaths = list(self.__openDBs.keys())
        try:
            filepaths.remove(self.tmp_filepath)
        except ValueError:
            pass
        return filepaths

    def checkOpening(self, filepath):
        """
        Check if a database can be open.

        :Parameter filepath: the full path of the file
        """
        try:
            # Check if file doesn't exist
            if os.path.isdir(filepath):
                error = translate('DBsTreeModel',
                                  'Openning cancelled: {0} is a folder.',
                                  'A logger error message').format(filepath)
                raise ValueError

            elif not os.path.isfile(filepath):
                error = translate('DBsTreeModel',
                                  'Opening failed: file {0} cannot be found.',
                                  'A logger error message').format(filepath)
                raise ValueError

            # Check if file is already open.
            elif self.getDBDoc(filepath) is not None:
                error = translate('DBsTreeModel',
                                  'Opening cancelled: file {0} already open.',
                                  'A logger error message').format(filepath)

                raise ValueError

        except ValueError:
            log.error(error)
            return False

        # Check the file format
        try:
            if not tables.is_hdf5_file(filepath):
                error = translate('DBsTreeModel',
                                  'Opening cancelled: file {0} has not HDF5 format.',
                                  'A logger error message').format(filepath)
                log.error(error)
                return False
        except (tables.NodeError, OSError):
            error = translate('DBsTreeModel',
                              """Opening failed: I cannot find out if file {0} has HDF5 """
                              """format.""",
                              'A logger error message').format(filepath)
            log.error(error)
            return False
        else:
            return True

    def openDBDoc(self, filepath, mode='a', position=0):
        """
        Open an existing hdf5 file and load it into the tree model.

        :Parameters:

        - `filepath`: full path of the database file we wish to open.
        - `mode`: the opening mode of the database file. It can be 'r'ead-only
          'w'rite or 'a'ppend
        """
        is_open = False
        if self.checkOpening(filepath):
            # Open the database and add it to the tracking system
            db_doc = dbdoc.DBDoc(filepath, mode)
            self.mapDB(filepath, db_doc)

            # Populate the model with the dbdoc
            root_node = rootgroupnode.RootGroupNode(self, db_doc, self.root)
            self.fdelta = frozenset([root_node])
            self.gdelta = frozenset([])
            self.ldelta = frozenset([])
            self.links_delta = frozenset([])
            self.insertRows(position, 1)
            is_open = True

        return is_open

    def closeDBDoc(self, filepath):
        """
        Close the hdf5 file with the given file path.

        The temporary database can't be closed by the user. It is
        automatically closed when the application exits.

        :Parameter filepath: the full path of the file being closed
        """

        for row, child in enumerate(self.root.children):
            if child.filepath == filepath:
                # Deletes the node from the tree of databases model/view
                self.remove_rows(row)

                # If needed, refresh the copied node info
                try:
                    if self.ccni['filepath'] == filepath:
                        self.ccni = {}
                except KeyError:
                    pass

                # Close the hdf5 file
                db_doc = self.getDBDoc(filepath)
                if db_doc.hidden_group is not None:
                    db_doc.h5file.remove_node(db_doc.hidden_group,
                                              recursive=True)
                db_doc.closeH5File()
                # Update the dictionary of open files
                self.removeMappedDB(filepath)
                break

    def createDBDoc(self, filepath, is_tmp_db=False):
        """
        Create a new, empty database (:meth:`vitables.h5db.dbdoc.DBDoc`
        instance).

        :Parameters:

        - `filepath`: the full path of the file being created.
        - `is_tmp_db`: True if the `DBDoc` is tied to the temporary database
        """

        try:
            QtWidgets.qApp.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.WaitCursor))
            # Create the dbdoc
            try:
                db_doc = dbdoc.DBDoc(filepath, 'w', is_tmp_db)
            except (tables.NodeError, OSError):
                log.error(
                    translate('DBsTreeModel',
                              """File creation failed due to unknown"""
                              """reasons! Please, have a look to the """
                              """last error displayed in the logger. If you """
                              """think it's a bug, please report it to """
                              """developers.""", 'A file creation error'))
                return None

            # Track the just created dbdoc
            self.mapDB(filepath, db_doc)

            # Populate the model with the dbdoc
            root = rootgroupnode.RootGroupNode(self, db_doc, self.root,
                                               is_tmp_db)
            self.fdelta = frozenset([root])
            self.gdelta = frozenset([])
            self.ldelta = frozenset([])
            self.links_delta = frozenset([])
            self.insertRows(0, 1)
        finally:
            QtWidgets.qApp.restoreOverrideCursor()
        return db_doc

    def __createTempDB(self):
        """
        Create a temporary database where filtered tables will be stored.

        The database will have a hidden group where cut nodes can be
        stored until they are pasted somewhere else.
        """

        # Create the database
        log.info(
            translate('DBsTreeModel', 'Creating the Query results file...',
                      'A logger info message'))
        (f_handler, filepath) = tempfile.mkstemp('.h5', 'FT_')
        os.close(f_handler)
        self.tmp_filepath = vitables.utils.forwardPath(filepath)
        db_doc = self.createDBDoc(self.tmp_filepath, True)
        return db_doc

    def deleteNode(self, index):
        """Delete a node.

        Delete the selected node from the model and from the database
        where it lives.

        :Parameter index: the index of the selected node
        """

        try:
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            # Deletes the node from the database
            node.editor().delete(node.nodepath)

            # Deletes the node from the tree of databases model/view
            parent = self.parent(index)
            position = node.row()
            self.remove_rows(position, parent=parent)

            # If needed, refresh the copied node info. This info must
            # not be cleared when pasting a CUT node overwrites other
            # node
            try:
                if self.ccni['is_copied'] and \
                        (self.ccni['filepath'] == node.filepath) and \
                        self.ccni['nodepath'].startswith(node.nodepath):
                    self.ccni = {}
            except KeyError:
                pass
        finally:
            QtWidgets.qApp.restoreOverrideCursor()

    def copy_node(self, index):
        """Mark a node from the tree of databases view as copied.

        :Parameter index: the index of the selected node
        """

        try:
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            self.ccni = {'is_copied': True,
                         'nodename': node.name,
                         'filepath': node.filepath,
                         'nodepath': node.nodepath,
                         'target': getattr(node, 'target', None)}
        finally:
            QtWidgets.qApp.restoreOverrideCursor()

    def cutNode(self, index):
        """Cut a `tables.Node`.

        The cut node is stored in a hidden group of its database.

        :Parameter index: the index of the selected node
        """

        try:
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            self.ccni = {'is_copied': False,
                         'nodename': node.name,
                         'filepath': node.filepath,
                         'nodepath': node.nodepath,
                         'target': getattr(node, 'target', None)}

            # Moves the node to a hidden group in its database
            node.editor().cut(node.nodepath)

            # Deletes the node from the tree of databases model/view
            parent = self.parent(index)
            position = index.row()
            self.remove_rows(position, parent=parent)
            # If position > 0 then the above sibling will be selected
            # else the parent group will be selected
            if position == 0:
                current = parent
            else:
                current = self.index(position - 1, 0, parent)
            self.vtgui.dbs_tree_view.selectNode(current)
        finally:
            QtWidgets.qApp.restoreOverrideCursor()

    def pasteNode(self, index, childname, overwrite=False):
        """Paste a tables.Node.

        Paste the last copied/cut node under the currently selected group.

        :Parameters:

        - `index`: the index of the selected node (the parent group)
        - `childname`: the name of the node being pasted
        - `overwrite`: True if a node is being overwritten
        """

        try:
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            parent = self.nodeFromIndex(index)

            # If the overwritten node (if any) exists in the tree of
            # databases view then delete it
            if overwrite:
                self.overwriteNode(parent, index, childname)

            # Paste the copied/cut node in the destination database
            db_doc = self.getDBDoc(parent.filepath)
            if self.ccni['target']:
                editor = tlink_editor.TLinkEditor(db_doc)
            else:
                editor = tnode_editor.TNodeEditor(db_doc)

            src_node = self.copiedNode()
            editor.paste(src_node, parent.node, childname)

            # Paste the node in the tree of databases model/view
            self.lazyAddChildren(index)
            parent.updated = True

            # Select the pasted node
            self.selectIndex(index, childname)
        finally:
            QtWidgets.qApp.restoreOverrideCursor()

    def copiedNode(self):
        """The tables.Node currently copied/cut.
        """

        src_filepath = self.ccni['filepath']
        if self.ccni['is_copied']:
            src_nodepath = self.ccni['nodepath']
        else:
            dirname = self.getDBDoc(src_filepath).hidden_group
            basename = self.ccni['nodename']
            src_nodepath = '{0}/{1}'.format(dirname, basename)

        return self.getDBDoc(src_filepath).get_node(src_nodepath)

    def create_group(self, index, childname, overwrite=False):
        """Create a `tables.Group` under the given parent.

        :Parameters:

        - `index`: the index of the parent node
        - `childname`: the name of the group being created
        - `overwrite`: True if a node is being overwritten
        """

        try:
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            parent = self.nodeFromIndex(index)
            # If the overwritten node (if any) exists in the tree of
            # databases view then delete it
            if overwrite:
                self.overwriteNode(parent, index, childname)

            # Create the group in the PyTables database
            parent.editor().create_group(parent.nodepath, childname)

            # Paste the node in the tree of databases model/view
            self.lazyAddChildren(index)
            parent.updated = True

            # Select the pasted node
            self.selectIndex(index, childname)
        finally:
            QtWidgets.qApp.restoreOverrideCursor()

    def rename_node(self, index, new_name, overwrite=False):
        """Rename a node.

        :Parameters:

        - `index`: the index of the node being renamed
        - `new_name`: the new name of the node
        - `overwrite`: True if a node is being overwritten
        """

        try:
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            initial_nodepath = node.nodepath
            parent_index = self.parent(index)
            parent = self.nodeFromIndex(parent_index)
            if overwrite:
                self.overwriteNode(parent, parent_index, new_name)

            # Rename the node in the PyTables database
            node.editor().rename(node.nodepath, new_name)

            # Rename the node in the databases tree view
            # The renamed node's children must be updated too
            self.updateDBTree(index, new_name, node)

            # If needed, refresh the copied node info
            try:
                if self.ccni['filepath'] == node.filepath:
                    if self.ccni['nodepath'].startswith(initial_nodepath):
                        self.ccni = {}
            except KeyError:
                pass
        finally:
            QtWidgets.qApp.restoreOverrideCursor()

    def updateDBTree(self, index, new_name, node):
        """
        After renaming a PyTables node update the tree of databases model/view.

        The following data must be updated:

            - name (DisplayRole)
            - nodepath (UserRole+1)
            - status tip (StatusTipRole)

        :Parameters:

        - `index`: the index of the node being renamed
        - `new_name`: the new name of the node
        - `node`: the node being renamed
        """

        # Update the renamed tree item
        self.setData(index, new_name, QtCore.Qt.DisplayRole)
        old_nodepath = node.nodepath
        dirname = os.path.split(old_nodepath)[0]
        new_nodepath = \
            ('{0}/{1}'.format(dirname, new_name)).replace('//', '/')
        self.setData(index, new_nodepath, QtCore.Qt.UserRole + 1)
        if hasattr(node, 'target'):
            self.setData(index, '{0}'.format(node.node),
                         QtCore.Qt.StatusTipRole)
        else:
            self.setData(index,
                         '{0}->{1}'.format(node.filepath, new_nodepath),
                         QtCore.Qt.StatusTipRole)

        # Update the item children, if any
        for child_index in self.walkTreeView(index):
            child_node = self.nodeFromIndex(child_index)
            child_nodepath = child_node.nodepath.replace(old_nodepath,
                                                         new_nodepath, 1)
            self.setData(child_index, child_nodepath, QtCore.Qt.UserRole + 1)
            if hasattr(child_node, 'target'):
                self.setData(child_index, '{0}'.format(child_node.node),
                             QtCore.Qt.StatusTipRole)
            else:
                self.setData(child_index,
                             '{0}->{1}'.format(child_node.filepath,
                                               child_node.nodepath),
                             QtCore.Qt.StatusTipRole)

    def move_node(self, src_filepath, childpath, parent_index, overwrite=False):
        """Move a `tables.Node` to a different location.

        :Parameters:

          - `src_filepath`: the full path of the source database
          - `childpath`: the full path of the node being moved
          - `parent_index`: the model index of the new parent group
          - `overwrite`: True if a node is being overwritten
        """

        try:
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            parent_node = self.nodeFromIndex(parent_index)
            # full path of the destination database and new parent
            dst_filepath = parent_node.filepath
            parentpath = parent_node.nodepath

            #
            # Check if the nodename is already in use
            #
            (nodename, overwrite) = self.validateNodename(
                src_filepath, childpath, dst_filepath, parentpath)
            if nodename is None:
                return nodename

            # If the overwritten node (if any) exists in the tree of
            # databases view then delete it
            if overwrite:
                self.overwriteNode(parent_node, parent_index, nodename)

            # Move the node to the PyTables database
            pt_node = self.getDBDoc(src_filepath).get_node(childpath)
            db_doc = self.getDBDoc(src_filepath)
            if hasattr(pt_node, 'target'):
                editor = tlink_editor.TLinkEditor(db_doc)
            else:
                editor = tnode_editor.TNodeEditor(db_doc)
            movedname = editor.move(childpath, self.getDBDoc(dst_filepath),
                                    parentpath, nodename)
        finally:
            QtWidgets.qApp.restoreOverrideCursor()
            return movedname

    def validateNodename(self, src_filepath, childpath, dst_filepath,
                         parentpath):
        """

        :Parameters:

          - `childpath`: the full path of the node being moved
          - `dst_filepath`: the full path of the destination database
          - `parentpath`: the full path of the new parent group
        """

        nodename = os.path.basename(childpath)
        dst_dbdoc = self.getDBDoc(dst_filepath)
        parent = dst_dbdoc.get_node(parentpath)
        sibling = getattr(parent, '_v_children').keys()

        # Nodename pattern
        pattern = "[a-zA-Z_]+[0-9a-zA-Z_ ]*"
        info = [translate('DBsTreeModel',
                          'Node move: nodename already exists',
                          'A dialog caption'),
                translate('DBsTreeModel',
                          """Source file: {0}\nMoved node: {1}\n"""
                          """Destination file: {2}\nParent group: {3}\n\n"""
                          """Node name '{4}' already in use in that group.\n""",
                          'A dialog label').format
                (src_filepath, childpath, dst_filepath,
                    parentpath, nodename),
                translate('DBsTreeModel', 'Rename', 'A button label')]

        # Validate the nodename
        nodename, overwrite = vitables.utils.getFinalName(
            nodename, sibling, pattern, info)
        self.vtgui.editing_dlg = True
        return nodename, overwrite

    def overwriteNode(self, parent_node, parent_index, nodename):
        """Delete from the tree of databases a node being overwritten.

        :Parameters:

          - `parent_node`: the parent of the overwritten node
          - `parent_index`: the model index of the new parent group
          - `nodename`: the name of the node being deleted
        """

        child = parent_node.findChild(nodename)
        child_index = self.index(child.row(), 0, parent_index)
        self.deleteNode(child_index)

    def walkTreeView(self, index):
        """Iterates over a subtree of the tree of databases view.

        :Parameter index: the model index of the root node of the iterated
            subtree
        """

        for prow in range(0, self.rowCount(index)):
            child = self.index(prow, 0, index)
            yield child
            for crow in range(0, self.rowCount(child)):
                yield self.index(crow, 0, child)

    def indexChildren(self, index):
        """Iterate over the children of a given index.

        :Parameter index: the model index whose children are being retrieved
        """

        for row in range(0, self.rowCount(index)):
            yield self.index(row, 0, index)

    def selectIndex(self, parent, name):
        """Select in the tree view the index with the given parent and name.

        :Parameters:

            - `parent`: the parent of the model index being selected
            - `name`: the name tied to the model index being selected
        """

        for child in self.indexChildren(parent):
            node = self.nodeFromIndex(child)
            if node.name == name:
                self.vtgui.dbs_tree_view.selectNode(child)

    def updateTreeFromData(self, parent_index=None):
        """Update tree of expanded nodes from hdf5 data.

        This function should be used if the structure of a file was
        updated through pytables functions. It is better to use model
        functions but they need to be better documented and expanded
        to be usefull. This function is a temporary fix.

        """
        parent_index = parent_index if parent_index else QtCore.QModelIndex()
        self.lazyAddChildren(parent_index)
        for index in self.indexChildren(parent_index):
            self.updateTreeFromData(index)

    def flags(self, index):
        """Returns the item flags for the given index.

        This is a reimplemented function used by the model to indicate
        to views which items can be dragged, and which will accept drops.

        :Parameter index: the index of a given item.
        """

        # Every item in the model is enabled and selectable
        default_flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        if not index.isValid():
            return default_flags

        node = self.nodeFromIndex(index)
        node_kind = node.node_kind
        # If a database is in read-only mode items cannot be edited
        db_doc = self.getDBDoc(node.filepath)
        if db_doc.mode == 'r':
            flags = default_flags
        # The root group of a database cannot be moved or renamed
        elif node_kind == 'root group':
            flags = QtCore.Qt.ItemIsDropEnabled | default_flags
        # A regular group of a database can be moved, renamed and dropped
        elif node_kind == 'group':
            flags = QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled \
                | QtCore.Qt.ItemIsEditable | default_flags
        # A leaf of a database can be moved and renamed but not dropped
        else:
            flags = QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEditable \
                | default_flags

        return flags

    def data(self, index, role):
        """Returns the data stored under the given role for the item
        referred to by the index.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """
        if not index.isValid():
            data = None
            return data
        node = self.nodeFromIndex(index)
        if role in _ROLE_NODE_GET_FUNCTION_DICT:
            return _ROLE_NODE_GET_FUNCTION_DICT[role](node)
        else:
            return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """Sets the role data for the item at index to value.

        :Parameters:

        - `index`: the index of a data item
        - `value`: the value to be set
        - `role`: the role being set
        """

        if not index.isValid():
            result = False
        node = self.nodeFromIndex(index)
        if role == QtCore.Qt.DisplayRole:
            node.name = value
            self.dataChanged.emit(index, index)
            result = True
        elif role == QtCore.Qt.StatusTipRole:
            node.as_record = value
            self.dataChanged.emit(index, index)
            result = True
        elif role == QtCore.Qt.DecorationRole:
            node.icon = value
            self.dataChanged.emit(index, index)
            result = True
        elif role == QtCore.Qt.UserRole:
            node.filepath = value
            self.dataChanged.emit(index, index)
            result = True
        elif role == QtCore.Qt.UserRole + 1:
            node.nodepath = value
            self.dataChanged.emit(index, index)
            result = True
        elif role == QtCore.Qt.UserRole + 2:
            node.node_kind = value
            self.dataChanged.emit(index, index)
            result = True
        else:
            result = False
        return result

    def headerData(self, section, orientation, role):
        """Returns the data for the given role and section in the header
        with the specified orientation.

        :Parameters:

        - `section`: the header section being inspected
        - `orientation`: the header orientation (horizontal or vertical)
        - `role`: the role of the header section being inspected
        """

        if (orientation, role) == (QtCore.Qt.Horizontal,
                                   QtCore.Qt.DisplayRole):
            return translate('DBsTreeModel',
                             'Tree of databases',
                             'Header of the only column of the tree of databases view')

        return None

    def columnCount(self, index):
        """The number of columns for the children of the given index.

        :Parameter index: the model index being inspected.
        """
        return 1

    def rowCount(self, index):
        """The number of rows of the given model index.

        :Parameter index: the model index being inspected.
        """

        node = self.nodeFromIndex(index)
        if node == self.root:
            nrows = len(node)
        else:
            nrows = 0
            if node.node_kind in ('group', 'root group'):
                nrows = len(node)
        return nrows

    def hasChildren(self, index):
        """Finds out if a node has children.

        The goal of this reimplementation is to provide an inexpensive
        way for views to check for the presence of children and draw the
        appropriate decoration for their parent item.

        The decoration (if any) consists in the small +/- symbols used
        for expanding/collpasing the node. In principle, it is painted
        only if the node's children have been added.
        As we populate our model in a lazy way (see :meth:`lazyAddChildren`
        and :meth:`vitables.h5db.dbstreeview.DBsTreeView.updateExpandedGroup`
        methods) we want the decoration to be painted whenever the node has
        children, *even if the children have not been added to the model yet
        (so we can't use the underlying data store, we must use the data
        source). This way the user will know that the node has children*.

        :Parameter index: the index of the node being inspected.
        """

        if not index.isValid():  # self.root fulfils this condition
            return True
        parent = self.nodeFromIndex(index)
        if hasattr(parent.node, '_v_nchildren'):
            return getattr(parent.node, '_v_nchildren')
        else:
            return False

    def index(self, row, column, parent):
        """Creates an index in the model for a given node and returns it.

        This is a reimplementation of the index method. It creates an
        index for a tree node (i.e. :meth:`RootGroupNode`, :meth:`GroupNode`
        and :meth:`LeafNode` instances) specified by a row, a column and a
        parent index.

        Every node except the root one will be tied to an index by this
        method.

        :Parameters:

        - `row`: the row of the node relative to its parent
        - `column`: the column of the node relative to its parent
        - `parent`: the index of the node's parent
        """

        if self.hasIndex(row, column, parent):
            group = self.nodeFromIndex(parent)
            try:
                node = group.childAtRow(row)
                return self.createIndex(row, column, node)
            except IndexError:
                return QtCore.QModelIndex()
        return QtCore.QModelIndex()

    def nodeFromIndex(self, index):
        """Retrieves the tree node with a given index.

        :Parameter index: the index of a tree node
        """

        if index.isValid():
            return index.internalPointer()
        else:
            return self.root

    def parent(self, child):
        """The parent index of a given index.

        :Parameter child: the child index whose parent is being retrieved.
        """

        node = self.nodeFromIndex(child)
        if node is self.root:
            return QtCore.QModelIndex()
        parent = node.parent
        if parent is self.root:
            return QtCore.QModelIndex()
        grandparent = parent.parent
        row = grandparent.rowOfChild(parent)
        return self.createIndex(row, 0, parent)

    def lazyAddChildren(self, index):
        """Add children to a group node when it is expanded.

        Lazy population of the model is partially implemented in this
        method. Expanded items are updated so that children items are added if
        needed. This fact improves enormously the performance when files
        whit a large number of nodes are opened.

        :Parameter index: the index of the activated item
        """

        if not index.isValid():
            return
        node = self.nodeFromIndex(index)
        if node.node_kind not in ('group', 'root group'):
            return
        group = node.node

        # Find out if children have to be added by comparing the
        # names of children currently added to model with the
        # names of the whole list of children
        model_children = frozenset([node.childAtRow(row).name
                                    for row in range(0, len(node))])
        children_groups = frozenset(getattr(group, '_v_groups').keys())
        children_leaves = frozenset(getattr(group, '_v_leaves').keys())
        children_links = frozenset(getattr(group, '_v_links').keys())
        self.gdelta = children_groups.difference(model_children)
        self.ldelta = children_leaves.difference(model_children)
        self.links_delta = children_links.difference(model_children)
        self.fdelta = frozenset([])
        new_children = (len(self.gdelta) + len(self.ldelta)
                        + len(self.links_delta))
        if not new_children:
            return
        else:
            self.insertRows(0, new_children, index)

    def insertRows(self, position=0, count=1, parent=QtCore.QModelIndex()):
        """Insert `count` rows before the given `position`.

        Inserted rows will be children of the item represented by the `parent`
        model index. This method is called during nodes population and when
        files are opened/created.

        Warning! This method is MONKEY PATCHED if the DBs Sorting plugin is
        enabled. If it is the case the working code will be in module
        vitables.plugins.dbstreesort.dbs_tree_sort

        :Parameters:

        - `position`: the position of the first row being added.
        - `count`: the number of rows being added
        - `parent`: the index of the parent item.

        :Returns: True if the row is added. Otherwise it returns False.
        """

        # Add rows to the model and update its underlaying data store
        self.layoutAboutToBeChanged.emit()
        first = position
        last = position + count - 1
        self.beginInsertRows(parent, first, last)
        node = self.nodeFromIndex(parent)
        for file_node in self.fdelta:
            self.root.insertChild(file_node, position)
        for name in self.gdelta:
            group = groupnode.GroupNode(self, node, name)
            node.insertChild(group, position)
        for name in self.ldelta:
            leaf = leafnode.LeafNode(self, node, name)
            node.insertChild(leaf, position)
        for name in self.links_delta:
            link = linknode.LinkNode(self, node, name)
            node.insertChild(link, position)
        self.dataChanged.emit(parent, parent)
        self.endInsertRows()
        self.layoutChanged.emit()

        # Report views about changes in data
        top_left = self.index(first, 0, parent)
        bottom_right = self.index(last, 0, parent)
        self.dataChanged.emit(top_left, bottom_right)

        return True

    def remove_rows(self, position, count=1, parent=QtCore.QModelIndex()):
        """Removes `count` rows before the given row.

        This method is called when an item is cut/deleted/D&D.

        :Parameters:

        - `position`: the position of the first row being removed.
        - `count`: the number of rows being removed
        - `parent`: the index of the parent item.

        :Returns: True if the row is removed. Otherwise it returns False.
        """

        # Remove rows from the model and update its underlaying data store
        self.layoutAboutToBeChanged.emit()
        first = position
        last = position + count - 1
        self.beginRemoveRows(parent, first, last)
        group = self.nodeFromIndex(parent)
        del group.children[position]
        self.dataChanged.emit(parent, parent)
        self.endRemoveRows()
        self.layoutChanged.emit()

        return True

    def closeViews(self, parent, start, end):
        """When a leaf with a view is about to be removed then close the view.

        :Parameters:

            - `parent`: model index under which items are going to be removed
            - `start`: position of the first removed index
            - `stop`: position of the last removed index
        """

        nodepaths = []
        for position in range(start, end + 1):
            node = self.nodeFromIndex(self.index(position, 0, parent))
            nodepaths.append(node.nodepath)
        filepath = node.filepath
        for window in self.vtgui.workspace.subWindowList():
            if window.dbt_leaf.filepath == filepath:
                wpath = window.dbt_leaf.nodepath
                for path in nodepaths:
                    if re.match(path, wpath):
                        window.close()
                        break

    def supportedDropActions(self):
        """Setup drag and drop behavior of the model."""
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def mimeTypes(self):
        """Returns a list of MIME types that can be used to describe a
        list of model indexes or a list of filepaths.
        """
        return ["application/x-dbstreemodeldatalist", "text/uri-list"]

    def mimeData(self, indexes):
        """Returns a QMimeData object that contains serialized items of data
        corresponding to the list of indexes specified.

        When a node is dragged the information required to drop it later on is
        encoded by this method and returned as a QMimeData object.

        :Parameter indexes: a list of indexes
        """

        mime_data = QtCore.QMimeData()
        encoded_data = QtCore.QByteArray()

        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.WriteOnly)

        # Only one item selections are allowed in the tree of databases
        # view so indexes contains always one element
        for index in indexes:
            if index.isValid():
                filepath = self.data(index, QtCore.Qt.UserRole)
                nodepath = self.data(index, QtCore.Qt.UserRole + 1)
                row = str(index.row())
                stream.writeQString(filepath)
                stream.writeQString(nodepath)
                stream.writeQString(row)

                self.initial_parent = self.parent(index)

        # Store the MIME type of the object and the encoded description of that
        # object in the QMimeData object
        mime_data.setData("application/x-dbstreemodeldatalist", encoded_data)
        return mime_data

    def dropMimeData(self, data, action, row, column, parent):
        """Handles the data supplied by a drag and drop operation that
        ended with the given action.

        :Parameters:

        - `data`: the data being dropped.
        - `action`: the action being performed (copy or move).
        - `row`: the row under the item where the operation ends.
        - `columns`: the column under the item where the operation ends.
        - `parent`: the index of the item where operation ends.

        :Returns: True if item is dropped. Otherwise it returns False.
        """

        # Examine the MIME type
        if not (data.hasFormat("application/x-dbstreemodeldatalist") or
                data.hasFormat("text/uri-list")):
            return False

        if action == QtCore.Qt.IgnoreAction:
            return True

        if column > 0:
            return False

        # If the dropped object is one or more files then open them
        if data.hasFormat("text/uri-list"):
            uris_list = data.urls()
            # Transform every element of the sequence into a path and open it
            for uri in uris_list:
                path = uri.path()
                if sys.platform.startswith('win'):
                    path = path[1:]
                if os.path.isfile(path):
                    self.vtapp.fileOpen(path)
            return True

        # If the dropped object is a tree node then update the tree
        parent_node = self.nodeFromIndex(parent)
        encoded_data = data.data("application/x-dbstreemodeldatalist")

        # Moving is not allowed if the parent group remains the same
        initial_parent = self.initial_parent
        if parent == initial_parent:
            return False

        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.ReadOnly)
        while not stream.atEnd():
            # Decode the encoded data
            filepath = stream.readQString()
            nodepath = stream.readQString()
            initial_row = int(stream.readQString())

            # A node cannot be moved on itself
            if (parent_node.filepath, parent_node.nodepath) == (filepath,
                                                                nodepath):
                return False

            # Move the node to its final destination in the PyTables database
            new_name = self.move_node(filepath, nodepath, parent)
            if new_name is None:
                return False

            # Remove the dragged node from the model
            self.remove_rows(initial_row, parent=initial_parent)

            # If needed, refresh the copied node info
            try:
                if self.ccni['filepath'] == filepath:
                    if self.ccni['nodepath'].startswith(nodepath):
                        self.ccni = {}
            except KeyError:
                pass

            # Add the dropped node to the model
            self.lazyAddChildren(parent)
            parent_node.updated = True

            # Select the pasted node
            self.selectIndex(parent, new_name)

        return True
