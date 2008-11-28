import unittest
import sys
import os

import tables

import qt

import vitables.nodes.arrayDoc as arrayDoc

class ArrayDocTestCase(unittest.TestCase):
    """Test case for the ArrayDoc class.
    """

    def setUp(self):
        """Open the sample hdf5 file and instantiate an ArrayDoc object."""

        filepath = os.path.abspath('tests/samples.h5')
        VTAPP.dbManager.openDB(filepath, mode='a')
        doc = VTAPP.dbManager.getDB(filepath)
        self.h5file = doc.getH5File()
        nodepath = '/array_samples/b'
        self.array = arrayDoc.ArrayDoc(doc, nodepath)
        self.scalar_array = arrayDoc.ArrayDoc(doc, '/array_samples/sna')


    def tearDown(self):
        """Close any open file."""
        VTAPP.slotFileCloseAll()


    def test01_arrayDocInstance(self):
        """Check whether the ArrayDoc class could be instantiated.
        """

        self.assert_(isinstance(self.array, arrayDoc.ArrayDoc), 'Unable to instantiate the ArrayDoc class for arrays.')


    def test02_getNodeName(self):
        """Check the Array name getter.
        """

        name = self.array.getNodeName()
        expected = self.h5file.root.array_samples.b.name
        self.assertEqual(name, expected, 'Unable to retrieve the Array name.')


    def test03_nodeTitle(self):
        """Check the Array title getter.
        """

        title = self.array.nodeTitle()
        expected = self.h5file.root.array_samples.b.title
        self.assertEqual(title, expected, 'Unable to retrieve the Array title.')


    def test04_getNodePathName(self):
        """Check if the Array full path can be retrieved.
        """

        node_path = self.array.getNodePathName()
        expected = self.h5file.root.array_samples.b._v_pathname
        self.assertEqual(node_path, expected, 'Unable to retrieve the Array full path.')


    def test05_getDataType(self):
        """Check if the Array classname can be retrieved.
        """

        dataType = self.array.getDataType()
        expected = self.h5file.root.array_samples.b.atom.type
        self.assertEqual(dataType, expected, 'Unable to find out the Array type class.')


    def test06_getFlavor(self):
        """Check if the Array flavor can be retrieved.
        """

        flavor = self.array.getFlavor()
        expected = self.h5file.root.array_samples.b.flavor
        self.assertEqual(flavor, expected, 'Unable to find out the Array flavor.')


    def test07_getShape(self):
        """Check if the Array shape can be retrieved.
        """

        shape = self.array.getShape()
        expected = self.h5file.root.array_samples.b.shape
        self.assertEqual(shape, expected, 'Unable to find out the Array shape.')


    def test08_getFilters(self):
        """Check if the filters attribute of the Array can be retrieved.
        """

        filters = self.array.getFilters()
        expected = self.h5file.root.array_samples.b.filters
        self.assertEqual(filters, expected, 'Unable to find out the Array shape.')


    def test09_numRows(self):
        """Check if the number of rows of the Array can be retrieved.
        """

        # Regular Array
        nrows = self.array.numRows()
        expected = self.h5file.root.array_samples.b.nrows
        self.assertEqual(nrows, expected, 'Bad number of rows for regular arrays.')

        # Array that contains a scalar numarray
        nrows = self.scalar_array.numRows()
        expected = 1
        self.assertEqual(nrows, expected, 'Bad number of rows for scalar numarrays.')


    def test10_numCols(self):
        """Check if the number of columns of the Array can be retrieved.
        """

        # Regular Array
        ncols = self.array.numCols()
        expected = 3
        self.assertEqual(ncols, expected, 'Bad number of cols for regular arrays.')

        # Array that contains a scalar numarray
        ncols = self.scalar_array.numRows()
        expected = 1
        self.assertEqual(ncols, expected, 'Bad number of cols for scalar numarrays.')


##    def test11_getNodeInfo(self):
##        """Check if the user attributes names of the node can be retrieved.
##        """
##
##        # Create a user attribute
##        raise NotImplementedError


class EArrayDocTestCase(unittest.TestCase):
    """Test case for the ArrayDoc class.
    """

    def setUp(self):
        """Open the sample hdf5 file and instantiate an ArrayDoc object."""

        filepath = os.path.abspath('tests/samples.h5')
        VTAPP.dbManager.openDB(filepath, mode='a')
        doc = VTAPP.dbManager.getDB(filepath)
        self.h5file = doc.getH5File()
        nodepath = '/array_samples/earray'
        self.earray = arrayDoc.ArrayDoc(doc, nodepath)


    def tearDown(self):
        """Close any open file."""
        VTAPP.slotFileCloseAll()


    def test01_arrayDocInstance(self):
        """Check whether the EArrayDoc class could be instantiated.
        """

        self.assert_(isinstance(self.earray, arrayDoc.ArrayDoc), 'Unable to instantiate the ArrayDoc class for enlargeable arrays.')


    def test02_getNodeName(self):
        """Check the EArray name getter.
        """

        name = self.earray.getNodeName()
        expected = self.h5file.root.array_samples.earray.name
        self.assertEqual(name, expected, 'Unable to retrieve the EArray name.')


    def test03_nodeTitle(self):
        """Check the EArray title getter.
        """

        title = self.earray.nodeTitle()
        expected = self.h5file.root.array_samples.earray.title
        self.assertEqual(title, expected, 'Unable to retrieve the EArray title.')


    def test04_getNodePathName(self):
        """Check if the EArray full path can be retrieved.
        """

        node_path = self.earray.getNodePathName()
        expected = self.h5file.root.array_samples.earray._v_pathname
        self.assertEqual(node_path, expected, 'Unable to retrieve the EArray full path.')


    def test05_getDataType(self):
        """Check if the EArray classname can be retrieved.
        """

        dataType = self.earray.getDataType()
        expected = self.h5file.root.array_samples.earray.atom.type
        self.assertEqual(dataType, expected, 'Unable to find out the EArray type class.')


    def test06_getFlavor(self):
        """Check if the EArray flavor can be retrieved.
        """

        flavor = self.earray.getFlavor()
        expected = self.h5file.root.array_samples.earray.flavor
        self.assertEqual(flavor, expected, 'Unable to find out the EArray flavor.')


    def test07_getShape(self):
        """Check if the EArray shape can be retrieved.
        """

        shape = self.earray.getShape()
        expected = self.h5file.root.array_samples.earray.shape
        self.assertEqual(shape, expected, 'Unable to find out the EArray shape.')


    def test08_getFilters(self):
        """Check if the filters attribute of the EArray can be retrieved.
        """

        filters = self.earray.getFilters()
        expected = self.h5file.root.array_samples.earray.filters
        self.assertEqual(filters, expected, 'Unable to get the EArray filters.')


    def test09_numRows(self):
        """Check if the number of rows of the Array can be retrieved.
        """

        nrows = self.earray.numRows()
        expected = self.h5file.root.array_samples.earray.nrows
        self.assertEqual(nrows, expected, 'Bad number of rows for EArrays.')


    def test10_numCols(self):
        """Check if the number of columns of the EArray can be retrieved.
        """

        ncols = self.earray.numCols()
        expected = 2
        self.assertEqual(ncols, expected, 'Bad number of cols for EArrays.')


##    def test11_getNodeInfo(self):
##        """Check if the user attributes names of the node can be retrieved.
##        """
##
##        # Create a user attribute
##        raise NotImplementedError


class VLArrayDocTestCase(unittest.TestCase):
    """Test case for the ArrayDoc class.
    """

    def setUp(self):
        """Open the sample hdf5 file and instantiate an ArrayDoc object."""

        filepath = os.path.abspath('tests/samples.h5')
        VTAPP.dbManager.openDB(filepath, mode='a')
        doc = VTAPP.dbManager.getDB(filepath)
        self.h5file = doc.getH5File()
        nodepath = '/array_samples/vlarray'
        self.vlarray = arrayDoc.ArrayDoc(doc, nodepath)


    def tearDown(self):
        """Close any open file."""

        try:
            VTAPP.slotFileCloseAll()
        except NameError:
            # Once test99 has been executed the tearDown has nothing to do
            pass


    def test01_arrayDocInstance(self):
        """Check whether the ArrayDoc class could be instantiated.
        """

        self.assert_(isinstance(self.vlarray, arrayDoc.ArrayDoc), 'Unable to instantiate the ArrayDoc class for variable length arrays.')


    def test02_getNodeName(self):
        """Check the VLArray name getter.
        """

        name = self.vlarray.getNodeName()
        expected = self.h5file.root.array_samples.vlarray.name
        self.assertEqual(name, expected, 'Unable to retrieve the VLArray name.')


    def test03_nodeTitle(self):
        """Check the VLArray title getter.
        """

        title = self.vlarray.nodeTitle()
        expected = self.h5file.root.array_samples.vlarray.title
        self.assertEqual(title, expected, 'Unable to retrieve the VLArray title.')


    def test04_getNodePathName(self):
        """Check if the VLArray full path can be retrieved.
        """

        node_path = self.vlarray.getNodePathName()
        expected = self.h5file.root.array_samples.vlarray._v_pathname
        self.assertEqual(node_path, expected, 'Unable to retrieve the VLArray full path.')


    def test05_getDataType(self):
        """Check if the VLArray classname can be retrieved.
        """

        dataType = self.vlarray.getDataType()
        expected = self.h5file.root.array_samples.vlarray.atom.type
        self.assertEqual(dataType, expected, 'Unable to find out the VLArray type class.')


    def test06_getFlavor(self):
        """Check if the VLArray flavor can be retrieved.
        """

        flavor = self.vlarray.getFlavor()
        expected = self.h5file.root.array_samples.vlarray.flavor
        self.assertEqual(flavor, expected, 'Unable to find out the VLArray flavor.')


    def test07_getShape(self):
        """Check if the EArray shape can be retrieved.
        """

        shape = self.vlarray.getShape()
        expected = self.h5file.root.array_samples.vlarray.shape
        self.assertEqual(shape, expected, 'Unable to find out the VLArray shape.')


    def test08_getFilters(self):
        """Check if the filters attribute of the VLArray can be retrieved.
        """

        filters = self.vlarray.getFilters()
        expected = self.h5file.root.array_samples.vlarray.filters
        self.assertEqual(filters, expected, 'Unable to get the VLArray filters.')


    def test09_numRows(self):
        """Check if the number of rows of the Array can be retrieved.
        """

        nrows = self.vlarray.numRows()
        expected = self.h5file.root.array_samples.vlarray.nrows
        self.assertEqual(nrows, expected, 'Bad number of rows for VLArrays.')


    def test10_numCols(self):
        """Check if the number of columns of the VLArray can be retrieved.
        """

        ncols = self.vlarray.numCols()
        expected = 1
        self.assertEqual(ncols, expected, 'Bad number of cols for VLArrays.')


##    def test11_getNodeInfo(self):
##        """Check if the user attributes names of the node can be retrieved.
##        """
##
##        # Create a user attribute
##        raise NotImplementedError


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
    DBM = VTAPP.dbManager
    VTAPP.gui.hide()


def suite():
    """Return a test suite consisting of all the test cases in the module."""

    globalSetup()
    suite1 = unittest.makeSuite(ArrayDocTestCase)
    suite2 = unittest.makeSuite(EArrayDocTestCase)
    suite3 = unittest.makeSuite(VLArrayDocTestCase)
    theSuite = unittest.TestSuite([suite1, suite2, suite3])
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
