import unittest
import sys
import os

import tables

import qt

import vitables.nodes.groupDoc as groupDoc

class GroupDocTestCase(unittest.TestCase):
    """Test case for the GroupDoc class.
    """

    def setUp(self):
        """Open the sample hdf5 file and instantiate a NodeDoc object."""

        filepath = os.path.abspath('tests/samples.h5')
        VTAPP.dbManager.openDB(filepath, mode='a')
        doc = VTAPP.dbManager.getDB(filepath)
        self.h5file = doc.getH5File()
        nodepath = '/array_samples'
        self.group = groupDoc.GroupDoc(doc, nodepath)


    def tearDown(self):
        """Close any open file."""

        try:
            VTAPP.slotFileCloseAll()
        except NameError:
            # Once test99 has been executed the tearDown has nothing to do
            pass


    def test01_groupDocInstance(self):
        """Check whether the GroupDoc class could be instantiated.
        """

        self.assert_(isinstance(self.group, groupDoc.GroupDoc), 
            'Unable to instantiate the GroupDoc class.')


    def test02_getNodeName(self):
        """Check the Group name getter.
        """

        name = self.group.getNodeName()
        expected = self.h5file.root.array_samples._v_name
        self.assertEqual(name, expected, 'Unable to retrieve the Group name.')


    def test03_nodeTitle(self):
        """Check the Group title getter.
        """

        title = self.group.nodeTitle()
        expected = self.h5file.root.array_samples._v_title
        self.assertEqual(title, expected, 'Unable to retrieve the Group title.')


    def test04_getNodePathName(self):
        """Check if the Group full path can be retrieved.
        """

        node_path = self.group.getNodePathName()
        expected = self.h5file.root.array_samples._v_pathname
        self.assertEqual(node_path, expected, 'Unable to retrieve the Group full path.')


    def test05_getFileObject(self):
        """Check if the hosting File can be retrieved.
        """

        file = self.group.getFileObject()
        expected = self.h5file.root.array_samples._v_file
        self.assert_(file is expected, 'Unable to find out the hosting File.')


    def test06_getGroupNodes(self):
        """Check if the dictionary of children groups can be retrieved.
        """

        gn = self.group.getGroupNodes()
        expected = self.h5file.root.array_samples._v_groups
        self.assertEqual(gn, expected, 'Unable to retrieve the dictionary of children groups.')


    def test07_getLeafNodes(self):
        """Check if the dictionary of children leaves can be retrieved.
        """

        ln = self.group.getLeafNodes()
        expected = self.h5file.root.array_samples._v_leaves
        self.assertEqual(ln, expected, 'Unable to retrieve the dictionary of children leaves.')


    def test08_getRootGroupInfo(self):
        """Check if some info about the root node can be retrieved.
        """

        root_info = self.group.getRootGroupInfo()
        expected = self.group.filepath
        self.assertEqual(root_info[2], expected, 'Retrieved an incorrect file path value.')
        expected = os.path.basename(self.group.filepath)
        self.assertEqual(root_info[1], expected, 'Retrieved an incorrect filename.')
        expected = 'PyTables file, size='
        self.assert_(root_info[0].startswith(expected), 'Retrieved an incorrect type value.')


##    def test09_getNodeInfo(self):
##        """Check if the number of rows of the Group can be retrieved.
##        """
##
##        # Regular Group
##        a = arrayDoc.GroupDoc(self.h5file.root.array_samples, filePath, '/samples/b')
##        nrows = a.numRows()
##        expected = self.h5file.root.array_samples.nrows
##        self.assertEqual(nrows, expected, 'Bad number of rows for regular arrays.')
##
##        # Group that contains a scalar numarray
##        a = arrayDoc.GroupDoc(self.h5file.root.array_samples.sna, filePath, '/samples/sna')
##        nrows = a.numRows()
##        expected = 1
##        self.assertEqual(nrows, expected, 'Bad number of rows for scalar numarrays.')


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
    theSuite.addTest(unittest.makeSuite(GroupDocTestCase))
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
