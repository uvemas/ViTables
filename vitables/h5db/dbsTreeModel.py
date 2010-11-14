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

"""
Here is defined the DBsTreeModel class.

Classes:

* DBsTreeModel(QtCore.QAbstractItemModel)

Methods:

* __init__(self, parent=None)
* mapDB(self, filepath, db_doc)
* removeMappedDB(self, filepath)
* getDBDoc(self, filepath)
* getDBList(self)
* checkOpening(self, filepath)
* openDBDoc(self, filepath, mode='a', position=0)
* closeDBDoc(self, filepath)
* createDBDoc(self, filepath, tmp_db=False)
* __createTempDB(self)
* columnCount(self, parent)
* deleteNode(self,index)
* copyNode(self,index)
* cutNode(self, index)
* pasteNode(self, index, childname, overwrite=False)
* createGroup(self, index, childname, overwrite=False)
* renameNode(self, index, new_name, overwrite=False)
* walkTreeView(self, index)
* moveNode(self, src_filepath, childpath, parent_index, overwrite=False)
* overwriteNode(self, parent_node, parent_index, nodename)
* lazyAddChildren(self, index)
* flags(self, index)
* data(self, index, role)
* setData(self, index, value, role=Qt.EditRole)
* headerData(self, section, orientation, role)
* columnCount(self, parent)
* rowCount(self, parent)
* hasChildren(self, index)
* index(self, row, column, parent)
* nodeFromIndex(self, index)
* parent(self, child)
* insertRows(self, position=0, count=1, parent=QtCore.QModelIndex())
* removeRows(self, position, count=1, parent=QtCore.QModelIndex())
* closeViews(self, parent, start, end)
* supportedDropActions(self)
* mimeTypes(self)
* mimeData(self, indexes)
* dropMimeData(self, data, action, row, column, parent)

Functions:

* trs(source, comment=None)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'DBsTreeModel'

import tempfile
import os
import sys
import re

import tables

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.h5db import dbDoc
from vitables.h5db import rootGroupNode
from vitables.h5db import groupNode
from vitables.h5db import leafNode


def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


class DBsTreeModel(QtCore.QAbstractItemModel):
    """
    The tree of databases model.

    The data is read and written from and to data sources (i.e., HDF5/PyTables
    files) by the model.
    """

    def __init__(self, parent=None):
        """Create the model.

        :Parameter parent: the parent of the model
        """

        QtCore.QAbstractItemModel.__init__(self, parent)

        # The underlying data structure used to populate the model
        self.root = rootGroupNode.RootGroupNode()
        # The dictionary of open databases
        self.__openDBs = {}

        # Create the temporary database that will contain filtered tables
        self.tmp_filepath = u''
        self.tmp_dbdoc = self.__createTempDB()

        self.copied_node_info = {}
        self.vtapp = parent

        self.rowsAboutToBeRemoved.connect(self.closeViews)


    def mapDB(self, filepath, db_doc):
        """Maps a file path with a DBDoc instance.

        :Parameters:

        - `filepath`: the full path of an open database.
        - `db_doc`: a DBDoc instance.
        """
        self.__openDBs[filepath] = db_doc


    def removeMappedDB(self, filepath):
        """Removes the DBDoc instance tied to a given file path.

        :Parameter filepath: the full path of an open database.
        """
        del self.__openDBs[filepath]


    def getDBDoc(self, filepath):
        """Returns the DBDoc instance tied to a given file path.

        :Parameter filepath: the full path of an open database.
        """

        if self.__openDBs.has_key(filepath):
            return self.__openDBs[filepath]
        else:
            return None


    def getDBList(self):
        """Returns the list of paths of files currently open.

        The temporary database is not included in the list.
        """

        filepaths = self.__openDBs.keys()
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
                error = trs('Openning cancelled: %s is a folder.',
                    'A logger error message') % filepath
                raise ValueError

            elif not os.path.isfile(filepath):
                error = trs('Opening failed: file %s cannot be found.',
                    'A logger error message') % filepath
                raise ValueError

            # Check if file is already open.
            elif self.getDBDoc(filepath) is not None:
                error = trs('Opening cancelled: file %s already open.',
                    'A logger error message') % filepath

                raise ValueError

        except ValueError:
            print error
            return False

        # Check the file format
        try:
            if not tables.isHDF5File(filepath):
                error = trs(\
                    'Opening cancelled: %s has not HDF5 format.', 
                    'A logger error message') % filepath
                print error
                return False
        except Exception:
            error = trs("""Opening failed: I cannot find """
                """out if %s has HDF5 format.""", 
                'A logger error message') % filepath
            print error
            return False
        else:
            return True


    def openDBDoc(self, filepath, mode='a', position=0):
        """
        Open an existing hdf5 file.

        :Parameters:

        - `filepath`: full path of the database file we wish to open.
        - `mode`: the opening mode of the database file. It can be 'r'ead-only
            'w'rite or 'a'ppend
        """


        if self.checkOpening(filepath):
            # Open the database and add it to model
            db_doc = dbDoc.DBDoc(filepath, mode)
            self.mapDB(filepath, db_doc)
            root_node = rootGroupNode.RootGroupNode(db_doc, self.root)
            self.fdelta = frozenset([root_node])
            self.gdelta = frozenset([])
            self.ldelta = frozenset([])
            self.insertRows(position, 1)


    def closeDBDoc(self, filepath):
        """
        Close the hdf5 file with the given file path.

        The temporary database shouldn't be closed by the user. It is
        automatically closed when the application exits.

        :Parameter filepath: the full path of the file being closed
        """

        if isinstance(filepath, QtCore.QString):
            filepath = unicode(filepath)

        for row, child in enumerate(self.root.children):
            if child.filepath == filepath:
                # Deletes the node from the tree of databases model/view
                self.removeRows(row)
                # Close the hdf5 file
                db_doc = self.getDBDoc(filepath)
                db_doc.closeH5File()
                # Update the dictionary of open files
                self.removeMappedDB(filepath)
                break


    def createDBDoc(self, filepath, is_tmp_db=False):
        """
        Create a new, empty database (DBDoc instance).

        :Parameters:

        - `filepath`: the full path of the file being created.
        - `is_tmp_db`: True if the DBDoc is tied to the temporary database
        """

        try:
            QtGui.qApp.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            try:
                db_doc = dbDoc.DBDoc(filepath, 'w', is_tmp_db)
                if is_tmp_db:
                    db_doc.tieToTempDB(db_doc)
                else:
                    db_doc.tieToTempDB(self.tmp_dbdoc)
                self.mapDB(filepath, db_doc)
                root = rootGroupNode.RootGroupNode(db_doc, self.root, 
                    is_tmp_db)
                self.fdelta = frozenset([root])
                self.gdelta = frozenset([])
                self.ldelta = frozenset([])
                self.insertRows(0, 1)
            except:
                db_doc = None
                print trs(
                    """\nFile creation failed due to unknown reasons!\n"""
                    """Please, have a look to the last error displayed in """
                    """the logger. If you think it's a bug, please report it"""
                    """ to developers.""",
                    'A file creation error')
        finally:
            QtGui.qApp.restoreOverrideCursor()
            return db_doc


    def __createTempDB(self):
        """
        Create a temporary database where filtered tables will be stored.

        The database will have a hidden group where cut nodes can be
        stored until they are pasted somewhere else.
        """

        # Create the database
        print trs('Creating the Query results file...',
            'A logger info message')
        (f_handler, filepath) = tempfile.mkstemp('.h5', 'FT_')
        os.close(f_handler)
        self.tmp_filepath = unicode(QtCore.QDir.fromNativeSeparators(filepath))
        db_doc = self.createDBDoc(self.tmp_filepath, True)
        return db_doc


    def deleteNode(self, index):
        """Delete a node.

        Delete the selected node from the model and from the database
        where it lives.

        :Parameter index: the index of the selected node
        """

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            # Deletes the node from the tree of databases model/view
            parent = self.parent(index)
            position = node.row()
            self.removeRows(position, parent=parent)
            # Deletes the node from the PyTables database
            self.getDBDoc(node.filepath).deleteNode(node.nodepath)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def copyNode(self, index):
        """Mark a node from the tree of databases view as copied.

        :Parameter index: the index of the selected node
        """

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            self.copied_node_info = {'is_copied': True, 'node': node, 
                'initial_filepath': node.filepath, 
                'initial_nodepath': node.nodepath}
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def cutNode(self, index):
        """Cut a tables.Node.

        The cut node is stored in a hidden group of its database.

        :Parameter index: the index of the selected node
        """

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            self.copied_node_info = {'is_copied': False, 'node': node, 
                'initial_filepath': node.filepath, 
                'initial_nodepath': node.nodepath}
            # Deletes the node from the tree of databases model/view
            parent = self.parent(index)
            # position = node.row()
            position = index.row()
            self.removeRows(position, parent=parent)
            # Moves the node to a hidden group in its database
            self.getDBDoc(node.filepath).cutNode(node.nodepath)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def pasteNode(self, index, childname, overwrite=False):
        """Paste a tables.Node.

        Paste the last copied/cut node under the currently selected group.

        :Parameters:

        - `index`: the index of the selected node (the parent group)
        - `childname`: the name of the node being pasted
        - `overwrite`: True if a node is being overwritten
        """

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            parent = self.nodeFromIndex(index)
            # If the overwritten node (if any) exists in the tree of
            # databases view then delete it
            if overwrite:
                self.overwriteNode(parent, index, childname)

            # Paste the copied/cut node in the destination database
            src_filepath = self.copied_node_info['node'].filepath
            if self.copied_node_info['is_copied']:
                src_nodepath = self.copied_node_info['node'].nodepath
            else:
                dirname = self.getDBDoc(src_filepath).hidden_group
                basename = self.copied_node_info['node'].name
                src_nodepath = '%s/%s' % (dirname, basename)
            self.getDBDoc(src_filepath).pasteNode(src_nodepath, 
                                                    parent.node, childname)
            # Paste the node in the view
            self.lazyAddChildren(index)
            parent.updated = True

            # Select the pasted node
            self.selectIndex(index, childname)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def createGroup(self, index, childname, overwrite=False):
        """Create a tables.Group under the given parent.

        :Parameters:

        - `index`: the index of the parent node
        - `childname`: the name of the group being created
        - `overwrite`: True if a node is being overwritten
        """

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            parent = self.nodeFromIndex(index)
            # If the overwritten node (if any) exists in the tree of
            # databases view then delete it
            if overwrite:
                self.overwriteNode(parent, index, childname)

            # Create the group in the PyTables database
            self.getDBDoc(parent.filepath).createGroup(parent.nodepath, 
                childname)

            # Paste the node in the view
            self.lazyAddChildren(index)
            parent.updated = True

            # Select the pasted node
            self.selectIndex(index, childname)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def renameNode(self, index, new_name, overwrite=False):
        """Rename a node.

        :Parameters:

        - `index`: the index of the node being renamed
        - `new_name`: the new name of the node
        - `overwrite`: True if a node is being overwritten
        """

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            parent_index = self.parent(index)
            parent = self.nodeFromIndex(parent_index)
            if overwrite:
                self.overwriteNode(parent, parent_index, new_name)

            # Rename the node in the PyTables database
            self.getDBDoc(node.filepath).renameNode(node.nodepath, 
                new_name)

            # Rename the node in the view
            # The renamed node's children must be updated too
            self.setData(index, new_name, QtCore.Qt.DisplayRole)
            old_nodepath = node.nodepath
            dirname = os.path.split(old_nodepath)[0]
            new_nodepath = ('%s/%s' % (dirname, new_name)).replace('//', '/')
            self.setData(index, new_nodepath, QtCore.Qt.UserRole+1)
            self.setData(index, '%s->%s' % (node.filepath, node.nodepath), 
                        QtCore.Qt.StatusTipRole)
            for child_index in self.walkTreeView(index):
                child_node = self.nodeFromIndex(child_index)
                child_nodepath = child_node.nodepath.replace(old_nodepath, 
                                                            new_nodepath, 1)
                self.setData(child_index, child_nodepath, QtCore.Qt.UserRole+1)
                self.setData(child_index, '%s->%s' % (child_node.filepath, 
                            child_node.nodepath), QtCore.Qt.StatusTipRole)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def moveNode(self, src_filepath, childpath, parent_index, overwrite=False):
        """Move a tables.Node to a different location.

        :Parameters:

        - `src_filepath': the full path of the source database
        - `childpath`: the full path of the node being moved
        - `parent_index`: the model index of the new parent group
        - `overwrite`: True if a node is being overwritten
        """

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            parent_node = self.nodeFromIndex(parent_index)
            # full path of the destination database and new parent
            dst_filepath = parent_node.filepath
            parentpath = parent_node.nodepath

            #
            # Check if the nodename is already in use
            #
            nodename = os.path.basename(childpath)
            dst_dbdoc = self.getDBDoc(dst_filepath)
            parent = dst_dbdoc.getNode(parentpath)
            sibling = getattr(parent, '_v_children').keys()
            # Nodename pattern
            pattern = "[a-zA-Z_]+[0-9a-zA-Z_ ]*"
            info = [trs('Node move: nodename already exists', 
                    'A dialog caption'), 
                    trs("""Source file: %s\nMoved node: %s\n"""
                        """Destination file: %s\nParent group: %s\n\n"""
                        """Node name '%s' already in use in that group.\n""", 
                        'A dialog label') % \
                        (src_filepath, childpath, dst_filepath, 
                        parentpath, nodename), 
                    trs('Rename', 'A button label')]
            # Validate the nodename
            nodename, overwrite = vitables.utils.getFinalName(nodename, 
                sibling, pattern, info)
            if nodename is None:
                # I don't know why but break raises a syntax error here so
                # I use return
                return nodename

            # If the overwritten node (if any) exists in the tree of
            # databases view then delete it
            if overwrite:
                self.overwriteNode(parent_node, parent_index, nodename)

            # Move the node to the PyTables database
            self.getDBDoc(src_filepath).moveNode(childpath,
                self.getDBDoc(dst_filepath), parentpath, nodename)
        finally:
            QtGui.qApp.restoreOverrideCursor()
            return nodename


    def overwriteNode(self, parent_node, parent_index, nodename):
        """Delete from the tree of databases view a node being overwritten.

        :Parameters:

        - `parent_node': the parent of the overwritten node
        - `parent_index`: the model index of the new parent group
        - `nodename`: the name of the node being deleted
        """

        child = parent_node.findChild(nodename)
        child_index = self.index(child.row(), 0, parent_index)
        self.deleteNode(child_index)


    def walkTreeView(self, index):
        """Iterates over a subtree of the tree of databases view.

        :Parameter index: the model index of the root node of the iterated subtree
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
                self.vtapp.dbs_tree_view.selectNode(child)


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
            data = QtCore.QVariant()
        node = self.nodeFromIndex(index)
        if role == QtCore.Qt.DisplayRole:
            data = QtCore.QVariant(node.name)
        elif role == QtCore.Qt.ToolTipRole:
            data = QtCore.QVariant('%s: %s' % (node.node_kind, node.name))
        elif role == QtCore.Qt.StatusTipRole:
            data = QtCore.QVariant(node.as_record)
        elif role == QtCore.Qt.DecorationRole:
            data = QtCore.QVariant(node.icon)
        elif role == QtCore.Qt.UserRole:
            data = QtCore.QVariant(node.filepath)
        elif role == QtCore.Qt.UserRole+1:
            data = QtCore.QVariant(node.nodepath)
        elif role == QtCore.Qt.UserRole+2:
            data = QtCore.QVariant(node.node_kind)
        else:
            data = QtCore.QVariant()
        return data


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
        elif role == QtCore.Qt.UserRole+1:
            node.nodepath = value
            self.dataChanged.emit(index, index)
            result = True
        elif role == QtCore.Qt.UserRole+2:
            node.node_kind = value
            self.dataChanged.emit(index, index)
            result = True
        else:
            result = False
        return result


    def headerData(self, section, orientation, role):
        """Returns the data for the given role and section in the header
        with the specified orientation.
        """

        if (orientation, role) == (QtCore.Qt.Horizontal, \
            QtCore.Qt.DisplayRole):
            return QtCore.QVariant(trs('Tree of databases',
                'Header of the only column of the tree of databases view'))

        return QtCore.QVariant()


    def columnCount(self, parent):
        """The number of columns for the children of the given index.
        """
        return 1


    def rowCount(self, index):
        """The number of rows of the given model index.

        :Parameter `index`: the model index being inspected.
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
        As we populate our model in a lazy way (see `lazyAddChildren`
        method below and `DBsTreeView.expandNode` method) we want the
        decoration to be painted whenever the node has children, *even if
        the children have not been added to the model yet (so we cannot
        use the underlying data store, we must use the data source). So
        the user will know that the node has children*.

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
        index for a tree node (i.e. RootGroupNode, GroupNode and LeafNode
        instances) specified by a row, a column and a parent index.

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
        group = node.node

        # Find out if children have to be added by comparing the
        # names of children currently added to model with the
        # names of the whole list of children
        model_children = frozenset([node.childAtRow(row).name \
            for row in range(0, len(node))])
        children_groups = frozenset(getattr(group, '_v_groups').keys())
        children_leaves = frozenset(getattr(group, '_v_leaves').keys())
        self.gdelta = children_groups.difference(model_children)
        self.ldelta = children_leaves.difference(model_children)
        self.fdelta = frozenset([])
        new_children = len(self.gdelta) + len(self.ldelta)
        if not new_children:
            return
        else:
            self.insertRows(0, new_children, index)


    def insertRows(self, position=0, count=1, parent=QtCore.QModelIndex()):
        """Insert `count` rows before the given row.

        This method is called during nodes population and when files are
        opened/created.

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
            group = groupNode.GroupNode(node, name)
            node.insertChild(group, position)
        for name in self.ldelta:
            leaf = leafNode.LeafNode(node, name)
            node.insertChild(leaf, position)
        self.dataChanged.emit(parent, parent)
        self.endInsertRows()
        self.layoutChanged.emit()

        # Report views about changes in data
        top_left = self.index(first, 0, parent)
        bottom_right = self.index(last, 0, parent)
        self.dataChanged.emit(top_left, bottom_right)

        return True


    def removeRows(self, position, count=1, parent=QtCore.QModelIndex()):
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
        for position in range(start, end+1):
            node = self.nodeFromIndex(self.index(position, 0, parent))
            nodepaths.append(node.nodepath)
        filepath = node.filepath
        for window in self.vtapp.workspace.subWindowList():
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
        list of model indexes.
        """

        types = QtCore.QStringList()
        types << "application/x-dbstreemodeldatalist" << "text/uri-list"
        return types


    def mimeData(self, indexes):
        """Returns an object that contains serialized items of data
        corresponding to the list of indexes specified.

        When a node is dragged the information required to drop it later
        on is encoded by this method and returned as a QMimeData object.
        """

        mime_data = QtCore.QMimeData()
        encoded_data = QtCore.QByteArray()

        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.WriteOnly)

        # Only one item selections are allowed in the tree of databases
        # view so indexes contains always one element
        for index in indexes:
            if index.isValid():
                filepath = self.data(index, QtCore.Qt.UserRole).toString()
                nodepath = self.data(index, QtCore.Qt.UserRole+1).toString()
                row = QtCore.QString(str(index.row()))
                stream << filepath << nodepath << row

                self.initial_parent = self.parent(index)

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

        if not (data.hasFormat("application/x-dbstreemodeldatalist") or 
                data.hasFormat("text/uri-list")):
            return False

        if action == QtCore.Qt.IgnoreAction:
            return True

        if column > 0:
            return False

        if data.hasFormat("text/uri-list"):
            # The encoded data is stored in a byte array with a trailing
            # NULL byte
            encoded_data = data.data("text/uri-list")
            # Convert the binary array into a string with suitable format
            uris_string = QtCore.QUrl.fromEncoded(encoded_data).toString()
            # Split the string using the apropriate separators
            uris_list = re.split(u'\r\n|\r|\n', unicode(uris_string))
            # Transform every element of the sequence into a path and open it
            for item in uris_list:
                uri = QtCore.QUrl(item)
                path = unicode(uri.path())
                if sys.platform.startswith('win'):
                    path = path[1:]
                if os.path.isfile(path):
                    self.vtapp.slotFileOpen(path)
            return True

        parent_node = self.nodeFromIndex(parent)
        encoded_data = data.data("application/x-dbstreemodeldatalist")

        # Moving is not allowed if the parent group remains the same
        initial_parent = self.initial_parent
        if parent == initial_parent:
            return False

        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.ReadOnly)
        while not stream.atEnd():
            # Decode the encoded data
            filepath = QtCore.QString()
            nodepath = QtCore.QString()
            initial_row = QtCore.QString()
            stream >> filepath >> nodepath >> initial_row

            filepath = unicode(filepath)
            nodepath = unicode(nodepath)
            initial_row = int(initial_row.toInt()[0])

            # A node cannot be moved on itself
            if (parent_node.filepath, parent_node.nodepath) == (filepath, 
                nodepath):
                return False

            # Move the node to its final destination in the PyTables database
            new_name = self.moveNode(filepath, nodepath, parent)
            if new_name == None:
                return False

            # Remove the dragged node from the model
            self.removeRows(initial_row, parent=initial_parent)

            # Add the dropped node to the model
            self.lazyAddChildren(parent)
            parent_node.updated = True

            # Select the pasted node
            self.selectIndex(parent, new_name)

        return True
