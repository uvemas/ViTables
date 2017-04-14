"""A unittest module for the dbManager.py module."""

import unittest
import sys
import os
    
import tables    
import qt

import vitables.utils
import vitables.h5db.dbDoc  as dbDoc
import vitables.h5db.dbView as dbView
import vitables.h5db.dbManager as dbManager    
import vitables.treeEditor.treeNode as treeNode
import vitables.treeEditor.treeView as treeView


class DBManagerTestCase(unittest.TestCase):
    """Test case for the DBManager class.
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


    #
    # Instantiation tests
    #

    def test01_dbmInstance(self):
        """Check whether the DBManager class could be instantiated.
        """

        self.assert_(isinstance(VTAPP.dbManager, dbManager.DBManager),
            'Unable to instantiate the DBManager class.')


    #
    # Temporary database tests
    #

    def test04_tmpDBExists(self):
        """Check the temporary database creation.
        """

        self.assert_(os.path.isfile(VTAPP.dbManager.tmp_filepath),
            'Unable to create the temporary database.')


    def test05_tmpDBTracked(self):
        """Check if the temporary database is tracked.
        """

        self.assert_(VTAPP.dbManager._openDB.has_key(VTAPP.dbManager.tmp_filepath),
            'The temporary database has not been tracked.')


    def test06_tmpDBFormat(self):
        """Check the temporary database format.
        """

        tmp_db = VTAPP.dbManager.tmp_dbdoc.getH5File()
        self.assertEqual(tmp_db._isPTFile, True,
            'The temporary database is not a PyTables file.')


    def test07_tmpDBHidden(self):
        """Check the hiden group of the temporary database.
        """

        tmp_db = VTAPP.dbManager.tmp_dbdoc.getH5File()
        self.assertEqual(tmp_db.isVisibleNode(VTAPP.dbManager.hidden_where),
            False)


    def test08_tmpDBVisible(self):
        """Check the temporary database hierarchy.
        """

        tmp_db = VTAPP.dbManager.tmp_dbdoc.getH5File()
        list_nodes = tmp_db.listNodes('/')
        self.assertEqual(list_nodes, [],
            'The temporary database should be empty.')


    #
    # Test general DBManager methods
    #
    
    def test09_openNonExistentDB(self):
        """Check if a non existent database can be open.
        """

        # Try to open a non existing file
        dbpath = os.path.abspath('array8.h5')
        creation_ok = VTAPP.dbManager.openDB(dbpath, 'r')
        self.assert_(not creation_ok, 'Trying to open a non existing file.')


    def test10_openRegularDB(self):
        """Check if a regular database can be open.
        """

        # Try to open a proper file
        VTAPP.slotFileCloseAll()
        creation_ok = VTAPP.dbManager.openDB(self.filepath, 'r')
        self.assert_(creation_ok,
            'The database %s cannot be opened in read mode.' % self.filepath)


    def test11_openAlreadyOpenDB(self):
        """Check if an already open database can be open.
        """

        # Try to open an already opened file
        VTAPP.dbManager.openDB(self.filepath, 'r')
        creation_ok = VTAPP.dbManager.openDB(self.filepath, 'r')
        self.assert_(not creation_ok, 'The database is already opened.')


    def test12_openFakeDB(self):
        """Check if a non HDF5 file can be open.
        """

        # Try to open a non PyTables/HDF5 file
        dbpath = 'examples/vitablesrc'
        creation_ok = VTAPP.dbManager.openDB(dbpath, 'r')
        self.assert_(not creation_ok, 'The database format is unreadable.')


    def test13_closeDB(self):
        """Check if an opened database can be closed.
        """

        VTAPP.dbManager.closeDB(self.filepath)
        self.assert_(not VTAPP.dbManager._openDB.has_key(self.filepath),
            'The database cannot be closed.')


    def test14_dbList(self):
        """Try to retrieve the list of open databases.
        """

        VTAPP.slotFileCloseAll()
        VTAPP.dbManager.openDB(self.filepath, 'r')
        db_list = VTAPP.dbManager.dbList()
        self.assertEqual(db_list, [self.filepath],
            'Recovered a wrong databases list.')


    def test15_getDBIfOpen(self):
        """Try to retrieve an open database from the tracking dictionary.
        """

        VTAPP.dbManager.openDB(self.filepath, 'r')
        dbdoc = VTAPP.dbManager.getDB(self.filepath)
        test = isinstance(dbdoc, dbDoc.DBDoc)
        self.assert_(test, 'The database %s cannot be get.' % self.filepath)


    def test16_getDBViewIfOpen(self):
        """Try to retrieve a view from the tracking dictionary.
        """

        VTAPP.dbManager.openDB(self.filepath, 'r')
        dbview = VTAPP.dbManager.getDBView(self.filepath)
        test = isinstance(dbview, dbView.DBView)
        self.assert_(test,
            'The view of the database %s cannot be get.' % self.filepath)


    def test17_getDBIfClosed(self):
        """Try to retrieve a closed database from the tracking dictionary.
        """

        # Getting a closed database should return None
        VTAPP.slotFileCloseAll()
        self.assertEqual(VTAPP.dbManager.getDB(self.filepath), None)


    def test18_getDBViewIfClosed(self):
        """Try to retrieve a fake view from the tracking dictionary.
        """

        # Getting a view from a closed database should raise a KeyError
        VTAPP.slotFileCloseAll()
        self.assertRaises(KeyError, VTAPP.dbManager.getDBView, self.filepath)


    def test19_getCutNodes(self):
        """Check the getCutNodes method.
        """

        # Add a couple of nodes to the hidden group
        tmp_db = VTAPP.dbManager.getDB(VTAPP.dbManager.tmp_filepath).getH5File()
        tmp_db.createGroup('/_p_cutNode', 'Group_A')
        tmp_db.createCArray('/_p_cutNode',  'Hidden_CArray',
            tables.IntAtom(), (3, 3))
        tmp_db.flush()
        cut_nodes = VTAPP.dbManager.getCutNodes()
        cut_nodes.sort()
        expected = ['Group_A', 'Hidden_CArray']
        self.assertEqual(cut_nodes,  expected,
            'The retrieved list of cut nodes is wrong')


    def test20_clearHiddenGroup(self):
        """Check the clearHiddenGroup method.
        """

        VTAPP.dbManager.clearHiddenGroup()
        self.assertEqual(VTAPP.dbManager.getCutNodes(), [],
            'The cut nodes are not properly deleted')


    def test21_createFile(self):
        """Check the createFile method.
        """

        filepath = 'tests/prova_dbm.h5'
        VTAPP.dbManager.createFile(filepath)
        test = VTAPP.dbManager._openDB.has_key(filepath)
        VTAPP.dbManager.closeDB(filepath)
        os.unlink(filepath)
        self.assert_(test, 'A new file cannot be created.')


    def test22_createFileMode(self):
        """Check the opening mode in createFile method.
        """

        filepath = 'tests/prova_dbm.h5'
        VTAPP.dbManager.createFile(filepath)
        mode = VTAPP.dbManager.getDB(filepath).getFileMode()
        expected = 'w'
        VTAPP.dbManager.closeDB(filepath)
        os.unlink(filepath)
        self.assertEqual(mode, expected,
            'The file has not been created with the right mode.')


    #
    # Test copy of files
    #

    def test35_copyFile(self):
        """Check the DBManager.copyFile method.
        """

        # Warning: this test is not complete. It doesn't really check
        # the contents of files

        dst_filepath = 'tests/prova_dbm.h5'
        if os.path.isfile(dst_filepath):
            os.unlink(dst_filepath)
        VTAPP.dbManager.copyFile(self.filepath, dst_filepath)
        src_h5file = self.doc.getH5File()
        dst_h5file = tables.openFile(dst_filepath)
        src_nodes = [node._v_pathname for node in src_h5file.walkNodes('/')]
        dst_nodes = [node._v_pathname for node in dst_h5file.walkNodes('/')]
        dst_h5file.close()
        os.unlink(dst_filepath)
        self.assertEqual(src_nodes, dst_nodes,
            'The file has not been properly copied.')


    #
    # Test group creation
    #

    def test37_createGroup(self):
        """Check the DBManager.createGroup method.
        """

        # Create a new group under the selected item. After the creation
        # the parent item remains selected
        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setSelected(root_item, 1)
        VTAPP.dbManager.createGroup(self.filepath, '/', 'test_group')

        # Tree pane level test
        tree_view.setOpen(tree_view.selectedItem(), True)
        group_item = tree_view.findItem('test_group', 0)
        self.assert_(group_item,
            'The node has not been added to the tree pane.')

        # Database level test
        h5file = self.doc.getH5File()
        node = h5file.get_node('/test_group')
        self.assert_(node, 'The group creation has failed.')

        # Leave source database unchanged
        h5file.remove_node('/test_group')


    #
    # Test cut node operation
    #

    def test40_cut(self):
        """Check the DBManager.cut method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # Create a group and cut it. After that no item is selected
        VTAPP.dbManager.createGroup(self.filepath, '/', 'test_group')
        group_item = tree_view.findItem('test_group', 0)
        tree_view.setSelected(group_item, True)
        VTAPP.dbManager.cut(self.doc, '/', 'test_group')

        # Database level tests
        h5file = self.doc.getH5File()
        self.assertRaises(tables.exceptions.NoSuchNodeError, h5file.get_node,
            '/test_group')

        tmp_dbdoc = VTAPP.dbManager.tmp_dbdoc
        tmp_h5file = tmp_dbdoc.getH5File()
        hidden_nodes = tmp_h5file.get_node('/_p_cutNode')._v_children.keys()
        self.assertEqual(hidden_nodes, ['test_group'],
            'Cut nodes are not properly hidden.')

        # Tree pane level test
        tree_view.setSelected(root_item, True)
        group_item = tree_view.findItem('test_group', 0)
        self.assert_(not group_item,
            'The cut node has not been removed from the tree!')


    #
    # Test paste node operation
    #

    def test42_paste(self):
        """Check the DBManager.paste method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem(os.path.basename(self.filepath), 0)
        tree_view.setSelected(root_item, True)

        # The node being pasted
        VTAPP.dbManager.createGroup(self.filepath, '/', 'test_group')

        # Paste the copied node under the selected tree view item
        src_nodepath = '/test_group'
        dst_nodepath = '/'
        final_name = 'new_group'
        VTAPP.dbManager.paste(self.doc, src_nodepath, self.doc, dst_nodepath, final_name)

        # Database level test
        h5file = self.doc.getH5File()
        list_nodes = h5file.root._v_children.keys()
        self.assert_('new_group' in list_nodes,
            'The source database should contain the pasted group.')

        # Tree pane level test
        group_item = tree_view.findItem('new_group', 0)
        self.assert_(group_item,
            'The node has not been pasted in the destination database tree.')

        # Leave source database unchanged
        h5file.remove_node('/test_group')
        h5file.remove_node('/new_group')


    def test45_rename(self):
        """Check the rename method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # The node being renamed
        VTAPP.dbManager.createGroup(self.filepath, '/', 'test_group')

        # Select the tree view item and rename it
        group_item = tree_view.findItem('test_group', 0)
        tree_view.setSelected(group_item, True)
        initial_name = 'test_group'
        final_name = 'renamed_group'
        VTAPP.dbManager.rename(self.doc, '/', final_name, initial_name)

        # Database level test
        h5file = self.doc.getH5File()
        list_nodes = h5file.root._v_children.keys()
        test = (initial_name not in list_nodes) and (final_name in list_nodes)
        self.assert_(test,
            'The node renaming has failed.')

        # Tree pane level test
        group_item = tree_view.findItem('renamed_group', 0)
        self.assert_(group_item, 'The node has not been renamed.')

        # Leave source database unchanged
        h5file.remove_node('/', final_name)


    def test48_delete(self):
        """Check the delete method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # The node to be deleted
        VTAPP.dbManager.createGroup(self.filepath, '/', 'outer_group')
        VTAPP.dbManager.createGroup(self.filepath, '/outer_group', 'inner_group')

        # Select the tree view item and delete it
        group_item = tree_view.findItem('outer_group', 0)
        tree_view.setSelected(group_item, True)
        VTAPP.dbManager.delete(self.doc, '/', 'outer_group')

        # Database level test
        list_nodes = self.doc.getH5File().root._v_children.keys()
        test = 'outer_group' not in list_nodes
        self.assert_(test, 'The node deletion has failed.')

        # Tree pane level test
        outer_item = tree_view.findItem('outer_group', 0)
        self.assert_(not outer_item,
            'The node has not been deleted from the tree pane.')


    def test99(self):
        """Exit ViTables."""

        global VTAPP
        VTAPP.slotFileExit()
        del VTAPP


def globalSetup():
    global QTAPP, VTAPP

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
    VTAPP.gui.hide()


def suite():
    """Return a test suite consisting of all the test cases in the module."""

    globalSetup()
    the_suite = unittest.TestSuite()
    the_suite.addTest(unittest.makeSuite(DBManagerTestCase))
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

    unittest.main(defaultTest='suite')

