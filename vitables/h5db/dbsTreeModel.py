# -*- coding: utf-8 -*-
#!/usr/bin/env python


########################################################################
#
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
#       $Id: dbsTreeModel.py 1080 2008-10-24 10:15:45Z vmas $
#
########################################################################

"""
Here is defined the DBsTreeModel class.

Classes:

* DBsTreeModel(QtCore.QAbstractItemModel)

Methods:

* __init__(self, parent=None)
* __createTempDB(self)
* __tr(self, source, comment=None)
* addNode(self, parent, child,row=0, index=QtCore.QModelIndex())
* checkOpening(self, filepath)
* closeDBDoc(self, filepath)
* columnCount(self, parent)
* copyNode(self,index)
* createDBDoc(self, filepath)
* createGroup(self, index, childname, overwrite=False)
* cutNode(self, index)
* data(self, index, role)
* deleteNode(self,index)
* dropMimeData(self, data, action, row, column, parent)
* flags(self, index)
* getDBDoc(self, filepath)
* getDBList(self)
* hasChildren(self, index)
* headerData(self, section, orientation, role)
* index(self, row, column, parent)
* lazyAddChildren(self, index)
* mapDB(self, filepath, db_doc)
* mimeData(self, indexes)
* mimeTypes(self)
* moveNode(self, src_filepath, childpath, dst_filepath, parentpath,
    childname=None)
* nodeFromIndex(self, index)
* openDBDoc(self, filepath, mode)
* overwriteNode(self, parent_node, parent_index, nodename)
* parent(self, index)
* pasteNode(self,index)
* removeMappedDB(self, filepath)
* removeRows(self, position, count=1, parent=QtCore.QModelIndex())
* renameNode(self, index, new_name)
* rowCount(self, parent)
* setData(self, index, value, role=QtCore.Qt.EditRole)
* supportedDropActions(self)
* walkTreeView(self, index)

Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import tempfile
import os
import sets
import re
import exceptions

import tables

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

import vitables.utils
from vitables.h5db import dbDoc
from vitables.h5db import rootGroupNode
from vitables.h5db import groupNode
from vitables.h5db import leafNode

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
        # and (under a hidden group) copied/cut nodes
        self.tmp_filepath = ''
        self.hidden_where = '/_p_cutNode'
        self.tmp_dbdoc = self.__createTempDB()

        self.copied_node_info = {}
        self.vtapp = parent

        self.connect(self, 
                QtCore.SIGNAL("rowsAboutToBeRemoved(QModelIndex, int, int)"), 
                self.closeViews)


    def __tr(self, source, comment=None):
        """Translate method."""
        return str(QtGui.qApp.translate('DBsTreeModel', source, comment))


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
        filepaths.remove(self.tmp_filepath)
        return filepaths


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
            elif self.getDBDoc(filepath) is not None:
                error = self.__tr('Opening cancelled: file %s already open.',
                    'A logger error message') % filepath
                raise ValueError, error

            # Check the file format
            else:
                try:
                    if not tables.isHDF5File(filepath):
                        raise ValueError
                except Exception, inst:
                    if type(inst) == exceptions.ValueError:
                        error = self.__tr(\
                            'Opening cancelled: %s has not HDF5 format.', 
                            'A logger error message') % filepath
                    else:
                        error = self.__tr("""Opening failed: I cannot find """
                            """out if %s has HDF5 format.""", 
                            'A logger error message') % filepath
                    raise ValueError, error
        except ValueError:
            print error
            return False
        else:
            return True


    def openDBDoc(self, filepath, mode='a'):
        """
        Open an existing hdf5 file.

        :Parameters:

        - `filepath`: full path of the database file we wish to open.
        - `mode`: the opening mode of the database file. It can be 'r'ead-only
            'w'rite or 'a'ppend
        """

        if isinstance(filepath, QtCore.QString):
            filepath = str(filepath)

        if self.checkOpening(filepath):
            # Open the database and add it to model
            db_doc = dbDoc.DBDoc(filepath, mode, self.tmp_dbdoc)
            self.mapDB(filepath, db_doc)
            root_node = rootGroupNode.RootGroupNode(db_doc, self.root)
            self.addNode(self.root, root_node)


    def closeDBDoc(self, filepath):
        """
        Close the hdf5 file with the given file path.

        The temporary database shouldn't be closed by the user. It is
        automatically closed when the application exits.

        :Parameter filepath: the full path of the file being closed
        """

        if isinstance(filepath, QtCore.QString):
            filepath = str(filepath)

        for row, child in enumerate(self.root.children):
            if child.filepath == filepath:
                # Deletes the node from the tree of databases model/view
                self.removeRows(row, 1)
                # Close the hdf5 file
                db_doc = self.getDBDoc(filepath)
                db_doc.closeH5File()
                # Update the dictionary of open files
                self.removeMappedDB(filepath)
                break


    def createDBDoc(self, filepath, tmp_db=False):
        """
        Create a new, empty database (DBDoc instance).

        :Parameters:

        - `filepath`: the full path of the file being created.
        - `tmp_db`: True if the DBDoc is tied to the temporary database
        """

        try:
            QtGui.qApp.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            try:
                if not tmp_db:
                    db_doc = dbDoc.DBDoc(filepath, 'w', self.tmp_dbdoc)
                else:
                    db_doc = dbDoc.DBDoc(filepath, 'w')
                self.mapDB(filepath, db_doc)
                root = rootGroupNode.RootGroupNode(db_doc, self.root, tmp_db)
                self.addNode(self.root, root)
            except:
                db_doc = None
                print self.__tr(
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
        print self.__tr('Creating the Query results file...',
            'A logger info message')
        (f_handler, self.tmp_filepath) = tempfile.mkstemp('.h5', 'FT_')
        os.close(f_handler)
        db_doc = self.createDBDoc(self.tmp_filepath, True)
        if not db_doc:
            return

        # Create the group where cut nodes will be stored
        h5file = db_doc.h5file
        try:
            h5file.createGroup('/', self.hidden_where[1:], 'Hide cut nodes')
            print self.__tr('OK!', 'Operation successful logger message')
            return db_doc
        except:
            vitables.utils.formatExceptionInfo()


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
            self.removeRows(position, 1, parent)
            # Deletes the node from the PyTables database
            self.getDBDoc(node.filepath).deleteNode(node.nodepath)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def copyNode(self, index):
        """Copy a Node.

        A copy of the node is stored in the hidden group of the temporary
        database. Note that prior to store the node, the hidden group is
        emptied.

        :Parameter index: the index of the selected node
        """

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            self.copied_node_info = {'is_copied': True, 
                'nodepath': node.nodepath, 'nodename': node.name, 
                'filepath': node.filepath, 
                'parent_nodepath': node.parent.filepath}
            # Copies the node to the hidden group of the temporary database
            self.getDBDoc(node.filepath).copyNode(node.nodepath)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def cutNode(self, index):
        """Cut a tables.Node.

        The cut node is stored in the hidden group of the temporary
        database. Note that prior to store the node, the hidden group is
        emptied.

        :Parameter index: the index of the selected node
        """

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            node = self.nodeFromIndex(index)
            self.copied_node_info = {'is_copied': False, 
                'nodepath': node.nodepath, 'nodename': node.name, 
                'filepath': node.filepath, 
                'parent_nodepath': node.parent.filepath}
            # Deletes the node from the tree of databases model/view
            parent = self.parent(index)
            position = node.row()
            self.removeRows(position, 1, parent)
            # Moves the node to the hidden group of the temporary database
            self.getDBDoc(node.filepath).cutNode(node.nodepath)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def pasteNode(self, index, childname, overwrite=False):
        """Paste a tables.Node.

        Paste the content of the hidden group of the temporary database.

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

            # Paste the node in the PyTables database
            self.getDBDoc(parent.filepath).pasteNode(parent.nodepath, 
                                                     childname)

            # Paste the node in the view
            self.lazyAddChildren(index)
            self.emit(QtCore.SIGNAL('nodeAdded'), index)
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
            self.emit(QtCore.SIGNAL('nodeAdded'), index)
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
            # If a node is overwritten, then deletion is followed by an
            # update of the `index` variable. The reason is that the node
            # being deleted and that being renamed exist both in the model
            # at the same time, so the index of the renamed node could
            # change after the deletion. It will happen if the deleted node
            # preceded the renamed one in the parent's list of children.
            # If the index has not changed then the update is a harmless
            # operation.
            if overwrite:
                self.overwriteNode(parent, parent_index, new_name)
                updated_row = parent.rowOfChild(node)
                index = self.index(updated_row, 0, parent_index)

            # Rename the node in the PyTables database
            self.getDBDoc(node.filepath).renameNode(node.nodepath, 
                new_name)

            # Rename the node in the view
            # The renamed node's children must be updated too
            self.setData(index, new_name, QtCore.Qt.DisplayRole)
            old_nodepath = node.nodepath
            dirname, old_nodename = os.path.split(old_nodepath)
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


    def walkTreeView(self, index):
        """Iterates over a subtree of the tree of databases view.

        :Parameter index: the model index of the root node of the iterated subtree
        """

        root = self.nodeFromIndex(index)
        if hasattr(root, 'children'):
            seq = root.children[:]
        else:
            seq = []
        while len(seq):
            child = seq.pop()
            child_index = self.index(child.row(), 0, index)
            yield child_index
            if hasattr(child, 'children'):
                for item_index in self.deepIterator(child_index):
                    yield item_index
        del seq


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
            # Bad nodename conditions
            nodename_in_sibling = nodename in sibling
            info = [self.__tr('Node move: nodename already exists', 
                    'A dialog caption'), 
                    self.__tr("""Source file: %s\nMoved node: %s\n"""
                        """Destination file: %s\nParent group: %s\n\n"""
                        """Node name '%s' already in use in that group.\n""", 
                        'A dialog label') % \
                        (src_filepath, childpath, dst_filepath, 
                        parentpath, nodename), 
                    self.__tr('Rename', 'A button label')]
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
        added_children = sets.Set([node.childAtRow(row).name \
            for row in range(0, len(node))])
        children_groups = sets.Set(getattr(group, '_v_groups').keys())
        children_leaves = sets.Set(getattr(group, '_v_leaves').keys())
        for name in children_groups.difference(added_children):
            child_group = groupNode.GroupNode(node, name)
            self.addNode(node, child_group, index=index)
        for name in children_leaves.difference(added_children):
            child_leaf = leafNode.LeafNode(node, name)
            self.addNode(node, child_leaf, index=index)

    def flags(self, index):
        """Returns the item flags for the given index.

        This is a reimplemented function used by the model to indicate
        to views which items can be dragged, and which will accept drops.

        :Parameter index: the index of a given item.
        """

        # Every item in the model is enabled and selectable
        default_flags = QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable

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
            return QtCore.QVariant()
        node = self.nodeFromIndex(index)
        if role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(node.name)
        elif role == QtCore.Qt.ToolTipRole:
            return QtCore.QVariant('%s: %s' % (node.node_kind, node.name))
        elif role == QtCore.Qt.StatusTipRole:
            return QtCore.QVariant(node.as_record)
        elif role == QtCore.Qt.DecorationRole:
            return QtCore.QVariant(node.icon)
        elif role == QtCore.Qt.UserRole:
            return QtCore.QVariant(node.filepath)
        elif role == QtCore.Qt.UserRole+1:
            return QtCore.QVariant(node.nodepath)
        elif role == QtCore.Qt.UserRole+2:
            return QtCore.QVariant(node.node_kind)
        else:
            return QtCore.QVariant()


    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """Sets the role data for the item at index to value.

        :Parameters:

        - `index`: the index of a data item
        - `value`: the value to be set
        - `role`: the role being set
        """

        if not index.isValid():
            return False
        node = self.nodeFromIndex(index)
        if role == QtCore.Qt.DisplayRole:
            node.name = value
            self.emit(QtCore.SIGNAL(
                'dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        elif role == QtCore.Qt.StatusTipRole:
            node.as_record = value
            self.emit(QtCore.SIGNAL(
                'dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        elif role == QtCore.Qt.DecorationRole:
            node.icon = value
            self.emit(QtCore.SIGNAL(
                'dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        elif role == QtCore.Qt.UserRole:
            node.filepath = value
            self.emit(QtCore.SIGNAL(
                'dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        elif role == QtCore.Qt.UserRole+1:
            node.nodepath = value
            self.emit(QtCore.SIGNAL(
                'dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        elif role == QtCore.Qt.UserRole+2:
            node.node_kind = value
            self.emit(QtCore.SIGNAL(
                'dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        return False


    def headerData(self, section, orientation, role):
        """Returns the data for the given role and section in the header
        with the specified orientation.
        """

        if (orientation, role) == (QtCore.Qt.Horizontal, \
            QtCore.Qt.DisplayRole):
            return QtCore.QVariant(self.__tr('Tree of databases',
                'Header of the only column of the tree of databases view'))

        return QtCore.QVariant()


    def columnCount(self, parent):
        """The number of columns for the children of the given index.
        """
        return 1


    def rowCount(self, parent):
        """The number of rows of the given index.

        :Parameter parent: the index of the node being inspected.
        """

        if not parent.isValid():
            parent_node = self.root
        else:
            parent_node = parent.internalPointer()
        return len(parent_node)


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
        decoration to be painted whenever the node has children, even if
        the children have not been added to the model yet. So the user
        will know that the node has children.

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

        group = self.nodeFromIndex(parent)
        node = group.childAtRow(row)
        return self.createIndex(row, column, node)


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

        :Parameter index: the child index whose parent is being retrieved.
        """

        node = self.nodeFromIndex(child)
        if node is None:
            return QtCore.QModelIndex()
        parent = node.parent
        if parent is None:
            return QtCore.QModelIndex()
        grandparent = parent.parent
        if grandparent is None:
            return QtCore.QModelIndex()
        row = grandparent.rowOfChild(parent)
        assert row != -1
        return self.createIndex(row, 0, parent)
    def addNode(self, parent, child, row=0, index=QtCore.QModelIndex()):
        """Adds a child node to a given parent.

        :Parameters:

        - `parent`: the parent node.
        - `child`: the node being inserted
        - `row`: the position of the first row being inserted.
        """

        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.beginInsertRows(index, row, 0)
        parent.insertChild(child)
        self.endInsertRows()
        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def removeRows(self, position, count=1, parent=QtCore.QModelIndex()):
        """Removes `count` rows before the given row.

        :Parameters:

        - `position`: the position of the first row being removed.
        - `count`: the number of rows being removed
        - `parent`: the index of the parent item.

        :Returns: True if the row is removed. Otherwise it returns False.
        """

        node = self.nodeFromIndex(parent)
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.beginRemoveRows(parent, position,
            position + count - 1)
        for row in range(count):
            del node.children[position + row]
        self.endRemoveRows()
        self.emit(QtCore.SIGNAL("layoutChanged()"))
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
            if window.leaf.filepath == filepath:
                wpath = window.leaf.nodepath
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
                node_kind = self.data(index, QtCore.Qt.UserRole+2).toString()
                name = self.data(index, QtCore.Qt.DisplayRole).toString()
                stream << filepath << nodepath << node_kind << name

                self.before_dragging_info = (self.parent(index),
                    index.internalPointer().row())

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
            uris = QtCore.QUrl.fromEncoded(encoded_data).toLocalFile()
            # Split the string using the apropriate separators
            uris_list = re.split('(\r\n)|\r|\n\0', str(uris))
            # Get rid of the separators
            filepaths = [uris_list[i] for i in range(0, len(uris_list) - 1, 2)]
            # Transform every element of the sequence into a path and open it
            for item in filepaths:
                path = str(QtCore.QUrl(item).path())
                self.vtapp.slotFileOpen(path)
            return True

        parent_node = self.nodeFromIndex(parent)
        encoded_data = data.data("application/x-dbstreemodeldatalist")

        # Moving is not allowed if the parent group remains the same
        (old_parent, dragged_node_position) = self.before_dragging_info
        if parent == old_parent:
            return False

        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.ReadOnly)
        while not stream.atEnd():
            # Decode the encoded data
            filepath = QtCore.QString()
            nodepath = QtCore.QString()
            node_kind = QtCore.QString()
            name = QtCore.QString()
            stream >> filepath >> nodepath >> node_kind >> name

            filepath = str(filepath)
            nodepath = str(nodepath)
            node_kind = str(node_kind)
            name = str(name)

            # Move the node to its final destination in the PyTables database
            new_name = self.moveNode(filepath, nodepath, parent)
            if new_name == None:
                return False

            # Update the children list of the dragged node's parent
            self.removeRows(dragged_node_position, 1, old_parent)

            # Insert the new node
            if node_kind == 'group':
                child = groupNode.GroupNode(parent_node, new_name)
            else:
                child = leafNode.LeafNode(parent_node, new_name)
            self.addNode(parent_node, child, index=parent)
            # self.emit(QtCore.SIGNAL('nodeAdded'), parent)

        return True



if __name__ == '__main__':
    import sys
    from vitables.h5db import dbsTreeView

    APP = QtGui.QApplication(sys.argv)
    DB_TREE_VIEW = dbsTreeView.DBsTreeView()

    # The tree of databases model
    DB_TREE_MODEL = DBsTreeModel()
    DB_TREE_VIEW.setModel(DB_TREE_MODEL)
    DB_TREE_VIEW.show()

    # Add some databases to the model
    BASEDIR = '/home/vmas/repositoris.nobackup/vitables_portingpyqt4/examples'
    FILEPATH = '%s/tutorial1.h5' % BASEDIR
    DB_TREE_MODEL.openDBDoc(FILEPATH, 'a')
    FILEPATH = '%s/array1.h5' % BASEDIR
    DB_TREE_MODEL.openDBDoc(FILEPATH, 'a')
#    FILEPATH = '%s/vlarray2.h5' % BASEDIR
#    DB_TREE_MODEL.openDBDoc(FILEPATH, 'r')
#    DB_TREE_MODEL.closeDBDoc(FILEPATH)
    APP.exec_()

