"""A unittest module for the dbView.py module."""

import unittest
import sys
import os

import tables

import qt

import vitables.utils
import vitables.h5db.dbView as dbView
import vitables.treeEditor.treeNode as treeNode
import vitables.treeEditor.treeView as treeView

class DBViewTestCase(unittest.TestCase):
    """Test case for the DBView class.
    """

    def setUp(self):
        """Open the sample hdf5 file."""

        self.filepath = os.path.abspath('tests/samples.h5')
        VTAPP.dbManager.openDB(self.filepath, mode='a')
        self.doc = VTAPP.dbManager.getDB(self.filepath)
        self.view = VTAPP.dbManager.getDBView(self.filepath)
        self.h5file = self.doc.getH5File()


    def tearDown(self):
        """Close any open file."""

        try:
            VTAPP.slotFileCloseAll()
        except NameError:
            # Once test99 has been executed the tearDown has nothing to do
            pass


    def test03_dbViewInstance(self):
        """Check whether the DBView class could be instantiated.
        """
        self.assert_(isinstance(self.view, dbView.DBView),
            'Unable to instantiate the DBView class.')


    #
    # DBView object tree general methods
    #

    def test30_dbViewRootItem(self):
        """Check whether the root_item attribute is created.
        """
        self.assert_(isinstance(self.view.root_item, treeNode.TreeNode),
            'Unable to create the root_item attribute.')


    def test31_dbViewCreateTree(self):
        """Check whether the object tree is created properly.

        This unittest checks both createTree and createQueryTree methods.
        """

        mode = self.doc.getFileMode()
        pixmap = self.view.root_item.pixmap(0)
        icons = vitables.utils.getIcons()
        if self.view.root_item.text(0).latin1() == 'Query results':
            icon_key = 'dbfilters'
        elif mode == 'r':
            icon_key = 'file_ro'
        else:
            icon_key = 'file_rw'
        expected_pixmap = icons[icon_key].pixmap(qt.QIconSet.Large,
            qt.QIconSet.Normal, qt.QIconSet.On)
        expected_expandable = True
        expected_where = '/'
        self.assertEqual(self.view.root_item.isExpandable(), expected_expandable,
            'The root_item should be expandable.')
        self.assertEqual(self.view.root_item.where, expected_where,
            'The root_item full path is not properly set.')
        self.assertEqual(self.view.root_item.pixmap(0).serialNumber(),
            expected_pixmap.serialNumber(),
            'The root_item pixmap is not properly set.')


    def test32_ExpandItem(self):
        """Check the slotExpandViewItem method.
        """

        # Count root item children before expanding it for the very first time
        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        initial_children = root_item.childCount()
        # Expand root item and count children again
        tree_view.setSelected(root_item, 1)
        tree_view.setOpen(root_item, True)
        final_children = root_item.childCount()

        # Tests
        root_node = self.doc.getNode('/')
        node_children = len(root_node._v_children.keys())
        self.assert_(not initial_children,
            "Not yet expanded root item shouldn't have any children")
        self.assertEqual(node_children, final_children,
            'Incorrect number of first level children')


    def test33_AddChild(self):
        """Check the addChild method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # An item not yet expanded. It should have no children
        parentname = 'array_samples'
        parent_item = tree_view.findItem(parentname, 0)
        children_before = parent_item.childCount()

        # The child that will be added. It shouldn't exist yet
        nodename = 'earray'
        item_before = tree_view.findItem(nodename, 0)

        # Add a child to the parent item
        node_path = '/%s/%s' % (parentname, nodename)
        self.view.addChild(node_path, parent_item)
        children_after = parent_item.childCount()
        item_after = tree_view.findItem(nodename, 0)

        # Tests
        self.assert_(not children_before,
            "The parent item shouldn't have any children yet.")
        self.assert_(children_after == 1,
            "The parent item should have only one child.")
        self.assert_(not item_before,
            'The item being added already exists.')
        self.assert_(item_after,
            'The item has not been added.')
        self.assert_(item_after.where == node_path,
            'The item where attribute has not been properly set.')
        # TODO: pixmap and drag and drop behavior should also be checked


    def test34_AddNode(self):
        """Check the addNode method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # The path of an item not yet added to the tree view
        parent_item_name = 'table_samples'
        parent_node_path = '/table_samples/inner_tables_group'
        nodename = 'inner_table'
        node_path = '%s/%s' % (parent_node_path, nodename)

        # The parent item shouldn't have any children still
        parent_item = tree_view.findItem(parent_item_name, 0)
        item_before = tree_view.findItem(nodename, 0)

        # Add the node
        node = self.view.addNode(node_path)
        item1_after = tree_view.findItem('inner_tables_group', 0)
        item2_after = tree_view.findItem(nodename, 0)
        tree_view.setSelected(item1_after, True)
        tree_view.setOpen(item1_after, True)
        tree_view.repaintContents()

        # Tests
        self.assert_(node,
            'The node has not been added.')
        self.assert_(not item_before,
            'The item being added already exists.')
        self.assert_(item1_after,
            'The item1 has not been added.')
        self.assert_(item2_after,
            'The item2 has not been added.')
        self.assertEqual('inner_tables_group/inner_table',
            ('%s/%s') % (item1_after.text(0).latin1(),
            item2_after.text(0).latin1()),
            'The added item has a wrong path')
        root_item = tree_view.findItem('samples.h5', 0)
        self.assert_(item1_after.parent() == parent_item,
            'The item1 has been added to the wrong parent.')


    #
    # Test group creation
    #

    def test39_CreateGroup(self):
        """Check the DBView.createGroup method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # The path of a group not yet created
        parentname = 'table_samples'
        parent_path = '/%s' % parentname
        nodename = 'new_group'
        node_path = '/%s/%s' % (parentname, nodename)

        # The group should not yet exist 
        parent_item = tree_view.findItem(parentname, 0)
        tree_view.setSelected(parent_item, 1)
        item_before = tree_view.findItem(nodename, 0)

        # Create a new group under the selected item. After the creation
        # the parent item remains selected
        self.view.createGroup(parent_path, nodename)
        item_after = tree_view.findItem(nodename, 0)

        # Tests
        self.assert_(not item_before,
            'The group being added already exists.')
        self.assert_(item_after,
            'The group has not been added.')
        self.assert_(item_after.where == node_path,
            'The item where attribute has not been properly set.')
        self.assert_(item_after.parent() == parent_item,
            'The item has been added to the wrong parent.')


    #
    # Test paste node operation
    #

    def test44_PasteSelected(self):
        """Check the DBView.CopyNode method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # Copy and paste the node at PyTables level
        parent_path = '/table_samples'
        final_name = 'pasted_item'
        h5file = self.doc.getH5File()
        parent_node = self.doc.getNode(parent_path)
        h5file.copyNode('/array_samples/earray', newparent=parent_node,
            newname=final_name, overwrite=True, recursive=True)
        parent_node._v_file.flush()

        # The item that will be copied and pasted in a different location
        parent_item = tree_view.findItem('array_samples', 0)
        tree_view.setOpen(parent_item, True)
        item_before = tree_view.findItem('earray', 0)

        # Select the parent where the copied item will be pasted
        parent_item = tree_view.findItem('table_samples', 0)
        tree_view.setSelected(parent_item, 1)
        # Paste a tree view item
        self.view.copyNode(self.filepath, item_before.where, self.filepath, parent_path, final_name)
        item_after = tree_view.findItem(final_name, 0)

        # Tests
        self.assert_(item_before,
            "The group being pasted doesn't exist.")
        self.assert_(item_after,
            'The item has not been pasted.')
        self.assert_(item_after.where == '/table_samples/pasted_item',
            'The item where attribute has not been properly set.')
        self.assert_(item_after.parent() == parent_item, 
            'The item has been pasted to the wrong parent.')

        # Leave source database unchanged
        h5file.removeNode('/table_samples/pasted_item')
        # TODO: drag and drop behavior should also be checked


    #
    # Test rename node operation
    #

    def test47_RenameSelected(self):
        """Check the renameSelected method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # The path of the node being renamed
        parent_path = '/'
        initial_name = 'array_samples'
        final_name = 'renamed_group'

        # Open the node to be renamed so its children are added to the
        # object tree
        item_before = tree_view.findItem(initial_name, 0)
        tree_view.setSelected(item_before, 1)
        tree_view.setOpen(item_before, 1)
        children_paths_before = []
        for item in treeView.deepLVIterator(item_before):
            children_paths_before.append(item.text(0))

        # Rename the node
        self.view.renameSelected(parent_path, final_name, initial_name)
        item_after = tree_view.findItem(final_name, 0)
        tree_view.setSelected(item_after, 1)
        tree_view.setOpen(item_after, 1)
        children_paths_after = []
        for item in treeView.deepLVIterator(item_after):
            children_paths_after.append(item.text(0))

        # Tests
        self.assert_(item_before,
            "The item being renamed hasn't been found.")
        self.assertEqual(children_paths_before, children_paths_after,
            'The children of the renamed item have wrong names.')
        children_pathnames = []
        renamed_path_ok = True
        for item in treeView.deepLVIterator(item_after):
            dirname = os.path.dirname(item.where)
            if dirname != '/renamed_group':
                renamed_path_ok = False
                break
        self.assert_(renamed_path_ok,
            "The children's where attribute has not been properly set.")


    #
    # Test delete node operation
    #

    def test50_Delete(self):
        """Check the delete method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # The name of the node being deleted
        nodename = 'table_samples'

        # Select node to be deleted
        item_before = tree_view.findItem(nodename, 0)
        tree_view.setSelected(item_before, 1)
        self.view.delete('/', nodename)
        item_after = tree_view.findItem(nodename, 0)

        # Tests
        self.assert_(item_before,
            "The item being deleted hasn't been found'.")
        self.assert_(not item_after,
            "The item has not been deleted.")


    def test99(self):
        """Exit ViTables."""

        global VTAPP
        VTAPP.slotFileExit()
        del VTAPP


def globalSetup():
    global QTAPP, VTAPP, VTApp

    # Avoid <QApplication: There should be max one application object> errors:
    # if an instance of QApplication already exists then use a pointer to it
    try:
        qt.qApp.argv()
        QTAPP = qt.qApp
    except RuntimeError:
        QTAPP = qt.QApplication(sys.argv)
    from vitables.vtapp import VTApp
    VTAPP = VTApp(keep_splash=False)
    QTAPP.setMainWidget(VTAPP.gui)
#    VTAPP.gui.hide()


def suite():
    """Return a test suite consisting of all the test cases in the module."""

    globalSetup()
    the_suite = unittest.TestSuite()
    the_suite.addTest(unittest.makeSuite(DBViewTestCase))
    return the_suite


if __name__ == '__main__':
    # ptdump output for samples.h5
    # / (RootGroup) ''
    # /array_samples (Group) 'A set of array samples'
    # /array_samples/a (Array(3L,)) 'A one row regular numpy'
    # /array_samples/b (Array(2L, 3L)) 'A regular numpy'
    # /array_samples/earray (EArray(6L, 2L)) 'Enlargeable array of Ints'
    # /array_samples/sna (Array()) 'A scalar numpy'
    # /array_samples/vlarray (VLArray(3L,)) 'Variable length array of Int64'
    # /table_samples (Group) 'A set of table samples'
    # /table_samples/empty_table (Table(0L,)) 'An empty table'
    # /table_samples/nested_table (Table(10L,), shuffle, zlib(1)) 'A nested table'
    # /table_samples/inner_tables_group (Group) ''
    # /table_samples/inner_tables_group/inner_table (Table(10L,), shuffle, zlib(1)) 'A table'

    # This unittest should be run several times with different MODE/self.view values
    # Run 1 MODE='a', self.view = self.doc.dbview
    # Run 2 MODE = 'r', self.view = self.doc.dbview
    # Run 3 self.view = DBM.getDBView(DBM.tmp_filepath)
    unittest.main(defaultTest='suite')
