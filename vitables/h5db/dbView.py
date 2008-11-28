# -*- coding: utf-8 -*-

########################################################################
#
#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
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
#       $Id: dbView.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the DBView class.

Classes:

* DBView (qt.QObject)

Methods:

* __init__(self, dbdoc, gui, tmp_db=False)
* __tr(self, source, comment=None)
* getRootItem(self)
* createTree(self, mode)
* createQueryTree(self)
* slotCollapseViewItem(self, item)
* slotExpandViewItem(self, item)
* addNode(self, node_path)
* addChild(self, child_path, parent_item)
* getNodeIcon(self, node)
* slotOnItem(self, item)
* slotShowStatusTip(self)
* checkSender(self, item)
* createGroup(self, where, name)
    def copyNode(self, src_filepath, src_where, target_filepath,
* cloneNode(self, source, new_parent, final_name)
    def move(self, src_filepath, src_where, target_filepath, target_parentpath,
* renameSelected(self, where, final_name, current_name)
* delete(self, where, name)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import os.path

import tables
import qt

from vitables.treeEditor.treeNode import TreeNode
from vitables.treeEditor import treeView
import vitables.utils

class DBView (qt.QObject):
    """
    The view binded to a given open file.
    Open databases (`DBDoc` instances) are displayed as top level items
    in the tree view pane of the application. Expanding these items we
    can see the complete object tree of the database.
    This class represents a view that is binded to a model (an open database.)
    """


    def __init__(self, dbdoc, gui, tmp_db=False):
        """
        Adds an open database to the tree view pane of the application.

        :Parameters:

        - `dbdoc`: a DBDoc instance
        - `gui`: the application main window
        - `tmp_db`: indicates if the view correspond to a temporary database
        """

        qt.QObject.__init__(self)

        self.dbdoc = dbdoc
        # The tables.File instance mapped to this view
        self.h5_file = self.dbdoc.getH5File()
        self.vtgui = gui
        self.icons = vitables.utils.getIcons()

        # A timer used to display tip info
        self.timer = qt.QTimer(self)
        self.pointed_item_path = ''
        if tmp_db:
            self.root_item = TreeNode(self, self.vtgui.otLV,
                self.__tr('Query results', 'A tree node label'))
            self.createQueryTree()
        else:
            self.root_item = TreeNode(self, self.vtgui.otLV,
                self.dbdoc.getFileName())
            self.createTree(self.dbdoc.getFileMode())

        # Connect qt.SIGNALs to slots
        self.connect(self.vtgui.otLV,
            qt.SIGNAL("expanded(QListViewItem *)"), self.slotExpandViewItem)
        self.connect(self.vtgui.otLV,
            qt.SIGNAL("collapsed(QListViewItem *)"),
            self.slotCollapseViewItem)
        self.connect(self.vtgui.otLV, qt.SIGNAL("onItem(QListViewItem *)"),
            self.slotOnItem)
        self.connect(self.timer, qt.SIGNAL('timeout()'), self.slotShowStatusTip)


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('DBView', source, comment).latin1()


    def getRootItem(self):
        """:Returns: the root tree view item"""
        return self.root_item


    def createTree(self, mode):
        """
        Create a view of the object tree of the database.

        The created tree view has only one item, the root one. Other
        items will be added on demand: when user expands a given
        group its children are added to the tree.
        The object tree is displayed using a qt.QListView so object tree
        nodes (groups and leaves) are represented as qt.QListViewItems.

        The tree view has one column labeled with node names.
        Items representing root nodes have an attribute named h5file
        that references the File instance whose object tree is being
        displayed. When access is needed to the node mapped to a
        given tree item, this attribute is used to get a reference to
        the node object.

        Every tree view item is drag enabled by default. Tree view items
        mapped to object tree groups are also drop enabled by default.

        :Parameter nodePaths:
            a list with the full path of every node of the object tree
        """

        self.root_item.setRenameEnabled(0, 0)
        if mode != 'r':
            xpm = self.icons['file_rw'].pixmap(qt.QIconSet.Large,
                qt.QIconSet.Normal, qt.QIconSet.On)
        else:
            xpm = self.icons['file_ro'].pixmap(qt.QIconSet.Large,
                qt.QIconSet.Normal, qt.QIconSet.On)
        self.root_item.setPixmap(0, xpm)
        # Setup drag and drop behavior
        self.root_item.setDnD('Group', 1)
        self.root_item.setExpandable(1)
        # Set the where attribute
        self.root_item.where = '/'


    #
    # These methods should only be called for temporary databases
    #
    def createQueryTree(self):
        """
        Add the qt.Query results tree to the tree pane.

        The qt.Query results tree represents the temporary file where
        filtered tables are stored. It has one column labeled with
        filtered table names.
        The root node has an attribute named h5file that references
        the File instance whose object tree is being displayed.
        When access is needed to the table mapped to a given tree
        item, this attribute is used to get a reference to the
        tables.Table object.
        """

        self.root_item.setRenameEnabled(0, 0)
        # Set icon
        self.root_item.setPixmap(0, 
            self.icons['dbfilters'].pixmap(qt.QIconSet.Large,
            qt.QIconSet.Normal, qt.QIconSet.On))
        # Setup drag and drop behavior
        self.root_item.setDropEnabled(0)
        self.root_item.setDragEnabled(0)
        self.root_item.setExpandable(1)
        # Set the where attribute
        self.root_item.where = '/'

    # ////////////////////////////////////////////////////////////////
    #
    # slots that update the tree pane
    #
    # ////////////////////////////////////////////////////////////////


    def slotCollapseViewItem(self, item):
        """
        Collapse a view item.

        This slot is connected to the "collapsed(qt.QListViewItem *)"
        qt.SIGNAL. The qt.SIGNAL is emited by the tree pane, so it can
        correspond to any existing dbview instance. This force us to
        check if a particular instance has or not to process the qt.SIGNAL.

        :Parameter item: the list view item being expanded
        """

        if not self.checkSender(item):
            return

        if not item.isExpandable():
            return

        # Set the group icon except for root nodes that have always 
        # the same icon
        if item.parent():
            item.setPixmap(0, self.icons['folder'].pixmap(qt.QIconSet.Large,
                qt.QIconSet.Normal, qt.QIconSet.On))


    def slotExpandViewItem(self, item):
        """
        Expand a view item.

        This slot is connected to the "expanded(qt.QListViewItem *)"
        qt.SIGNAL. The qt.SIGNAL is emited by the tree pane and references
        a given dbview instance. Other dbview instances should ignore
        the qt.SIGNAL. This force us to check if a particular instance has or
        not to process the qt.SIGNAL.

        Children are dinamically added to the expanded item.

        :Parameter item: the list view item being expanded
        """

        if not self.checkSender(item):
            return

        if not item.isExpandable():
            return

        # Set the group icon except for root nodes that have always the
        # same icon
        if item.parent():
            item.setPixmap(0,
                self.icons['folder_open'].pixmap(qt.QIconSet.Large,
                qt.QIconSet.Normal, qt.QIconSet.On))

        # The first level children of the expanded node. 
        children = self.h5_file.listNodes(item.where)

        # Adds the children to the tree view. Some of these
        # children may already exist in the tree view if the recover
        # last session is active (see vtapp.recoverLastSession method)
        for child in children:
            child_path = child._v_pathname
            child_exists = False
            # Add first level children of the regarded tree view item
            for child_item in treeView.flatLVIterator(item):
                if child_item.where == child_path:
                    child_exists = True
                    break
            if not child_exists:
                self.addChild(child_path, item)


    def addNode(self, node_path):
        """
        Add a node with a given path to the tree view.

        The addition is decomposed in several steps, one for every level
        of depth, and is done top to bottom. This way we ensure that the
        parent node exists before to add the child node. This method is
        called from vtapp.recoverLastSession().

        :Parameter node_path: the full path of the node being added
        """


        parent_path = '/'
        parent_item = self.root_item
        components = node_path.split('/')[1:]
        for item in components:
            child_path = ('%s/%s' % (parent_path, item)).replace('//', '/')
            child_item = self.addChild(child_path, parent_item)
            if not child_item:
                return False
            # The parent path and parent item of the item that will be added in
            # the next step
            parent_path = child_path
            parent_item = child_item

        # Check if every node in the path has been added
        for item in treeView.deepLVIterator(self.root_item):
            if item.where == node_path:
                return True
        return False


    def addChild(self, child_path, parent_item):
        """
        Add a child to a given node in the tree view.

        :Parameters:

        - `child_path`: the full path of the node being added
        - `parent_item`: the parent tree view item of the node being added
        """

        node_name = os.path.basename(child_path)

        # If the asked child already exists we do not create it
        for item in treeView.flatLVIterator(parent_item):
            if item.where == child_path:
                return item

        # If the requested node doesn't exist the do nothing
        node = self.dbdoc.getNode(child_path)
        if not isinstance(node, tables.Node):
            return False

        # Create the tree view item
        item = TreeNode(self, parent_item, node_name)
        icon = self.getNodeIcon(node)
        item.setPixmap(0, icon)
        # Setup drag and drop behavior
        if isinstance(node, tables.Group):
            item.setDnD('Group',  0)
        elif isinstance(node, tables.Leaf):
            item.setDnD('Leaf', 0)
        # Set the where attribute
        item.where = child_path
        return item


    def getNodeIcon(self, node):
        """
        Gets the item icon.

        This method gets the type of node mapped to the list view
        item. This info is used to set the pixmap of the list view.

        :Parameter node: the node being iconified

        :Returns: the pixmap mapped to the node type
        """

        icon_size = qt.QIconSet.Small
        # Get required info about node
        if isinstance(node, tables.Group):
            icon = 'folder'
            icon_size = qt.QIconSet.Large
        elif isinstance(node, tables.Table):
            icon = 'table'
        elif isinstance(node, tables.VLArray):
            # Support for both PyTables format version 1.x (in which
            # flavor can be VLString and Object) and PyTables format
            # version 2.x (in which those values are obsolete and the
            # PSEUDOATOM attribute has been introduced)
            flavor = node.flavor
            attrs = node.attrs
            if hasattr(attrs, 'PSEUDOATOM'):
                pseudoatom = attrs.PSEUDOATOM
            else:
                pseudoatom = None
            if (flavor == 'VLString') or (pseudoatom == 'vlstring'):
                icon = 'vlstring'
            elif (flavor == 'Object') or (pseudoatom == 'object'):
                icon = 'object'
            else:
                icon = 'vlarray'
        elif isinstance(node, tables.EArray):
            icon = 'earray'
        elif isinstance(node, tables.CArray):
            icon = 'carray'
        elif isinstance(node, tables.Array):
            icon = 'array'
        elif isinstance(node, tables.UnImplemented):
            icon = 'unimplemented'
#        else:
#            return qt.QPixmap()

        return self.icons[icon].pixmap(icon_size, qt.QIconSet.Normal,
            qt.QIconSet.On)


    # ////////////////////////////////////////////////////////////////
    #
    # slots that update the status bar
    #
    # ////////////////////////////////////////////////////////////////


    def slotOnItem(self, item):
        """
        Starts a timer.

        This slot is connected to the "onItem(qt.QListViewItem *)"
        qt.SIGNAL. The qt.SIGNAL is emited by the tree pane, so it can
        correspond to any existing dbview instance. This force us to
        check if a particular instance has or not to process the qt.SIGNAL.

        When the mouse pointer is placed over a tree view item for a few
        moments, a timer starts. When the timeout qt.SIGNAL is emited a tooltip
        with the node fullpath is displayed in the status bar.
        The single shot flag guarantees that the number of running timers at
        any time is at most 1 (because any pending timer is stopped when a
        new timer starts.) so, each time the message text is updated and the
        timer is restarted.

        :Parameter item: the pointed item
        """

        if not self.checkSender(item):
            return

        self.pointed_item_path = item.where
        self.timer.start(1000, 1)


    def slotShowStatusTip(self):
        """
        Shows a tool tip in the status bar giving information about the
        last tree node pointed by the mouse.
        """

        # The file and node full path
        self.vtgui.statusBar().clear()
        self.vtgui.statusBar().message(self.pointed_item_path, 3000)


    def checkSender(self, item):
        """
        Checks if a received qt.SIGNAL should or not be processed.

        Some slots of this class are connected to qt.SIGNALs emited by
        the tree pane. This qt.SIGNALs can be mapped to any existing
        dbview instance and should be processed only by that instance.
        """

        # Find out if this view should manage the received qt.SIGNAL
        sender = item.getFilepath()
        receiver = self.dbdoc.filepath
        if sender is receiver:
            return True


    # ////////////////////////////////////////////////////////////////
    #
    # Editing nodes
    #
    # Warning! These methods cannot rely in TreeView.selectedItem() for
    # finding the node being edited because, in a previous stage of the
    # node editing, the method LeavesManager.cleanLeavesUnderKey could
    # have been called. This method can potentially change the selected
    # item, leading to wrong results when editing nodes in the tree view
    #
    # ////////////////////////////////////////////////////////////////

    def createGroup(self, where, name):
        """
        Create a new group.

        Only regular groups can be created with this method. Root groups
        are created when the database is created (see DBManager class).

        :Parameters:

        - `where`: the full path of the parent node
        - `name`: the name of the group being created
        """

        # Find the parent node
        tree_pane = self.vtgui.otLV
        parent = treeView.findTreeItem(tree_pane, self.dbdoc.filepath, where)

        # If the group name is being used by other child node then
        # that node is removed
        for sibling in treeView.flatLVIterator(parent):
            sibling_name = os.path.basename(sibling.where)
            if sibling_name == name:
                sibling.parent().takeItem(sibling)
                del sibling
                self.vtgui.otLV.repaintContents()
                break

        # Create a non root, writable node
        group = TreeNode(self, parent, name)
        group.setPixmap(0, self.icons['folder'].pixmap(qt.QIconSet.Large,
            qt.QIconSet.Normal, qt.QIconSet.On))
        group.setDnD('Group', 0)
        group.where = tables.path.joinPath(where, name)

        # Ensure the new group is visible. An expanded signal is emited
        # what automatically updates the tree view
        self.vtgui.otLV.setOpen(parent, 1)


    def copyNode(self, src_filepath, src_where, target_filepath,
        target_parentpath, final_name):
        """
        Paste the copied/cut node into another location.

        :Parameters:

        - `src_filepath`: the full path of the source file
        - `src_where`: the full path of the copied node in the source file
        - `target_filepath`: the full path of the target file
        - `target_parentpath`: the path of the target group
        - `final_name`: the copied node will be pasted with this name
        """

        tree_pane = self.vtgui.otLV
        target = treeView.findTreeItem(tree_pane, target_filepath,
            target_parentpath)

        new_path = tables.path.joinPath(target_parentpath, final_name)

        # Overwrite nodes with the same name (if any)
        for sibling in treeView.flatLVIterator(target):
            if sibling.where == new_path:
                target.dbview.delete(target_parentpath, final_name)
                break

        # Clone the source node
        source = treeView.findTreeItem(tree_pane, src_filepath, src_where)
        if source:
            self.cloneNode(source, target, final_name)
        else:
	    pasted_item = target.dbview.addChild(new_path, target)
        # Update the clone text. This is a MUST because the item can have
        # been renamed due to an overwriting case
        tree_pane.setOpen(target, True)
        clone = treeView.findTreeItem(tree_pane, target_filepath, new_path)
        clone.setText(0, final_name)
        self.vtgui.otLV.repaintItem(target)
        

    def cloneNode(self, source, new_parent, final_name):
        """
        Clone a given tree view item under a new parent.

        :Parameters:

        - `source`: the node being cloned
        - `new_parent`: the parent node of the clone
        - `final_name`: the name of the clone
        """

        # The cloned item nodepath
        clone_path = tables.path.joinPath(new_parent.where, final_name)
        # Get the full paths of the source node and its children
        all_paths = [clone_path]
        for child in treeView.deepLVIterator(source):
            all_paths.append(child.where.replace(source.where, clone_path, 1))
        # Add the clone and its children to the new parent
        for nodepath in all_paths:
            new_parent.dbview.addNode(nodepath)


    def move(self, src_filepath, src_where, target_filepath, target_parentpath,
        final_name):
        """
        Drop the dragged node.

        :Parameters:

        - `src_filepath`: the full path of the source database
        - `src_where`: the full path in the source database of the moved node
        - `target_filepath`: the full path of the destination database
        - `target_parentpath`: the path of the target group
        - `final_name`: the moved node will be dropped with this name
        """

        # The source and target tree view items
        source = treeView.findTreeItem(self.vtgui.otLV, src_filepath, 
            src_where) 
        target = treeView.findTreeItem(self.vtgui.otLV, target_filepath, 
            target_parentpath)

        new_path = tables.path.joinPath(target_parentpath, final_name)

        # Overwrite nodes with the same name (if any)
        for sibling in treeView.flatLVIterator(target):
            if sibling.where == new_path:
                target.dbview.delete(target_parentpath, final_name)
                break

        # Update the source text. This is a MUST because the item can have
        # been renamed
        source.setText(0, final_name)
        # Update the where and dbview attribute of the source item and its
        # children
        old_path = src_where
        source.where = new_path
        source.dbview = target.dbview
        for child in treeView.deepLVIterator(source):
            (child_parent, childname) = os.path.split(child.where)
            new_parent = child_parent.replace(old_path, new_path, 1)
            child.where = tables.path.joinPath(new_parent, childname)
            child.dbview = target.dbview

        # Move the source to its final destination. 
        source.parent().takeItem(source)
        target.insertItem(source)
        self.vtgui.otLV.setSelected(self.vtgui.otLV.selectedItem(), False)
        self.vtgui.otLV.repaintContents()


    def renameSelected(self, where, final_name, current_name):
        """
        Rename the selected node in the tree pane.

        :Parameters:

        - `where`: the full path of the parent node
        - `current_name`: the node current name
        - `final_name`: the new node name
        """

        tree_pane = self.vtgui.otLV
        new_path = tables.path.joinPath(where, final_name)
 
        renamed_item = treeView.findTreeItem(tree_pane, self.dbdoc.filepath,
            tables.path.joinPath(where, current_name))
        parent = renamed_item.parent()
        # If the node being renamed has a sibling named final_name then
        # that sibling is removed
        for sibling in treeView.flatLVIterator(parent):
            if (sibling.where == new_path) and (sibling != renamed_item):
                parent.takeItem(sibling)
                del sibling
                break
 
        # Update the source item
        renamed_item.where = new_path
        renamed_item.setText(0, final_name)
        # Update the children of the source item
        current_path = tables.path.joinPath(where, current_name)
        for child in treeView.deepLVIterator(renamed_item):
            child.where = child.where.replace(current_path, new_path, 1)


    def delete(self, where, name):
        """
        Delete a given item from the tree pane.

        :Parameters:

        - `where`: the full path of the parent node
        - `name`: the name of the node being deleted
        """

        item = treeView.findTreeItem(self.vtgui.otLV, self.dbdoc.filepath,
            tables.path.joinPath(where, name))
        # move the item to the top-level and delete
        item.parent().takeItem(item)
        del item
        self.vtgui.otLV.repaintContents()
