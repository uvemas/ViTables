"""A unittest module for the dbDoc.py module."""

import unittest
import sys
import os

import tables
import qt

import vitables.h5db.dbDoc as dbDoc


class DBDocTestCase(unittest.TestCase):
    """Test case for the DBDoc class.
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


    def test02_dbDocInstance(self):
        """Check whether the DBDoc class could be instantiated.
        """
        self.assert_(isinstance(self.doc, dbDoc.DBDoc),
            'Unable to instantiate the DBDoc class.')


    def test13_closeH5File(self):
        """Check if the tables.File instance binded to the database is properly closed.
        """

        self.doc.closeH5File()
        self.assert_(not self.doc.getH5File().isopen,
            'The tables.File instance is not deleted after database closing.')


    #
    # DBDoc getter methods tests
    #

    def test23_getFileFormat(self):
        """Check the database format.
        """

        fmt = self.doc.getFileFormat()
        expected = 'PyTables file'
        self.assertEqual(fmt, expected, 'Unable to get the database format.')


    def test24_getFileName(self):
        """Check the database name.
        """

        filename = self.doc.getFileName()
        expected = os.path.basename(self.filepath)
        self.assertEqual(filename, expected,
            'Unable to get the database name.')


    def test25_getFileMode(self):
        """Check the database opening MODE.
        """

        mode = self.doc.getFileMode()
        expected = self.h5file.mode
        self.assertEqual(mode, expected,
            'Unable to get the database opening mode.')


    def test26_getH5File(self):
        """Check the tables.File instance binded to the database.
        """

        h5file = self.doc.getH5File()
        test1 = isinstance(h5file, tables.File)
        test2 = h5file.filename == self.filepath
        self.assert_(test1 and test2,
            'Unable to get the tables.File instance.')


    def test27_getH5FileCC(self):
        """Check the tables.File instance binded to the database (corner case).

        Corner case: try to open in write MODE a database when we have read-only permission.
        """

        # Database owned by root with permissions 644
        db_filepath = os.path.abspath('tests/root_owned_samples.h5')
        VTAPP.dbManager.openDB(db_filepath, 'a')
        db_doc = VTAPP.dbManager.getDB(db_filepath)
        h5file = db_doc.getH5File()
        test = h5file.mode == 'r'
        VTAPP.dbManager.closeDB(db_filepath)

        self.assert_(test, 'Bad tables.File instance MODE.')


    def test28_getNode(self):
        """Check the getNode mode.
        """

        nodepath = '/table_samples/nested_table'
        vt_path = self.doc.getNode(nodepath)._v_pathname
        test = nodepath == vt_path

        self.assert_(test, 'Retrieved the wrong node.')


    def test29_getNodeFake(self):
        """Check the getNode mode with non existent nodes.
        """

        nodepath = '/table_samples/fake_node'
        node = self.doc.getNode(nodepath)
        test = node == None

        self.assert_(test, 'Retrieved a non existent node!')


    #
    # Test copy of files
    #

    def test36_copyFile(self):
        """Check the DBDocc.copyFile method.
        """

        # Warning: this test is not complete. It doesn't really check
        # the contents of files

        dst_filepath = '/tmp/prova_dbm.h5'
        if os.path.isfile(dst_filepath):
            os.unlink(dst_filepath)
        self.doc.copyFile(dst_filepath)
        src_h5file = self.doc.getH5File()
        dst_h5file = tables.openFile(dst_filepath)
        src_nodes = [node._v_pathname for node in src_h5file.walkNodes('/')]
        dst_nodes = [node._v_pathname for node in dst_h5file.walkNodes('/')]
        src_nodes.sort()
        dst_nodes.sort()
        dst_h5file.close()
        os.remove(dst_filepath)
        self.assertEqual(src_nodes, dst_nodes,
            'The file has not been properly copied.')


    #
    # Test group creation
    #

    def test38_createGroup(self):
        """Check the DBDoc.createGroup method.
        """

        # Create a new group under the selected item. After the creation
        # the parent item remains selected
        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setSelected(root_item, 1)
        self.doc.createGroup('/', 'test_group')

        # Database level test
        h5file = self.doc.getH5File()
        node = h5file.getNode('/test_group')
        self.assert_(node, 'The group creation has failed.')

        # Tree pane level test
        group_item = tree_view.findItem('test_group', 0)
        self.assert_(group_item,
            'The node has not been added to the tree pane.')

        # Leave source database unchanged
        h5file.removeNode('/test_group')


    #
    # Test cut node operation
    #

    def test41_cut(self):
        """Check the DBDoc.cut method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setOpen(root_item, True)

        # The destination database
        tmp_dbdoc = VTAPP.dbManager.tmp_dbdoc
        tmp_h5file = tmp_dbdoc.getH5File()
        target_node = tmp_h5file.getNode('/_p_cutNode')

        # Create a group and cut it. After that no item is selected
        # The cut node will be stored in a hidden group in the temporary
        # database
        self.doc.createGroup('/', 'test_group')
        group_item = tree_view.findItem('test_group', 0)
        tree_view.setSelected(group_item, True)
        self.doc.cut('/', 'test_group', target_node)

        # Database level tests
        h5file = self.doc.getH5File()
        self.assertRaises(tables.exceptions.NoSuchNodeError, h5file.getNode,
            '/test_group')

        hidden_nodes = target_node._v_children.keys()
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

    def test43_paste(self):
        """Check the DBDoc.copyNode method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setSelected(root_item, 1)

        # The node being pasted
        self.doc.createGroup('/', 'test_group')

        # Paste the copied node under the selected tree view item
        src_nodepath = '/test_group'
        parent_path = '/'
        final_name = 'new_group'
        self.doc.copyNode(self.doc, src_nodepath, self.doc, parent_path, final_name)

        # Database level test
        h5file = self.doc.getH5File()
        list_nodes = h5file.root._v_children.keys()
        self.assert_('new_group' in list_nodes,
            'The destination database should contain the pasted group.')

        # Tree pane level test
        tree_view.setOpen(root_item, 1)
        group_item = tree_view.findItem('new_group', 0)
        self.assert_(group_item,
            'The node has not been pasted in the destination database tree.')

        # Leave source database unchanged
        h5file.removeNode('/test_group')
        h5file.removeNode('/new_group')


    #
    # Test paste node operation
    #

    def test46_rename(self):
        """Check the rename method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setSelected(root_item, 1)
        tree_view.setOpen(root_item, True)

        # The node being renamed
        self.doc.createGroup('/', 'test_group')

        # Select the tree view item and rename it
        group_item = tree_view.findItem('test_group', 0)
        tree_view.setSelected(group_item, True)
        initial_name = 'test_group'
        final_name = 'renamed_group'
        self.doc.rename('/', final_name, initial_name)

        # Database level test
        h5file = self.doc.getH5File()
        list_nodes = h5file.root._v_children.keys()
        test = (initial_name not in list_nodes) and (final_name in list_nodes)
        self.assert_(test,
            'The node renaming has failed.')

        # Tree pane level test
        tree_view.setOpen(root_item, True)
        group_item = tree_view.findItem('renamed_group', 0)
        self.assert_(group_item, 'The node has not been renamed.')

        # Leave source database unchanged
        h5file.removeNode('/', final_name)


    #
    # Test delete node operation
    #

    def test49_delete(self):
        """Check the delete method.
        """

        tree_view = VTAPP.gui.otLV
        root_item = tree_view.findItem('samples.h5', 0)
        tree_view.setSelected(root_item, 1)
        tree_view.setOpen(root_item, True)

        # The node to be deleted
        self.doc.createGroup('/', 'outer_group')
        self.doc.createGroup('/outer_group', 'inner_group')

        # Select the tree view item and delete it
        group_item = tree_view.findItem('outer_group', 0)
        tree_view.setSelected(group_item, True)
        # Rename a node using the name of an already present node
        self.doc.delete('/', 'outer_group')

        # PyTables level test
        list_nodes = self.doc.getH5File().root._v_children.keys()
        test = 'outer_group' not in list_nodes
        self.assert_(test, 'The node deletion has failed.')

        # Tree pane level test
        tree_view.setOpen(root_item, True)
        group_item = tree_view.findItem('outer_group', 0)
        self.assert_(not group_item, 
            'The node has not been deleted.')


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
    VTAPP.gui.hide()


def suite():
    """Return a test suite consisting of all the test cases in the module."""

    globalSetup()
    theSuite = unittest.TestSuite()
    theSuite.addTest(unittest.makeSuite(DBDocTestCase))
    return theSuite

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
