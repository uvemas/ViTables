import unittest
import sys
import os

import tables

import qt

import vitables.nodes.tableDoc as tableDoc

class TableDocTestCase(unittest.TestCase):
    """Test case for the TableDoc class.
    """

    def setUp(self):
        """Open the sample hdf5 file and instantiate a TableDoc object."""

        filepath = os.path.abspath('tests/samples.h5')
        VTAPP.dbManager.openDB(filepath, mode='a')
        doc = VTAPP.dbManager.getDB(filepath)
        self.h5file = doc.getH5File()
        nodepath = '/table_samples/nested_table'
        self.table = tableDoc.TableDoc(doc, nodepath)


    def tearDown(self):
        """Close any open file."""

        try:
            VTAPP.slotFileCloseAll()
        except NameError:
            # Once test99 has been executed the tearDown has nothing to do
            pass


    def test01_tableDocInstance(self):
        """Check whether the TableDoc class could be instantiated.
        """

        self.assert_(isinstance(self.table, tableDoc.TableDoc), 
            'Unable to instantiate the TableDoc class.')


    def test02_getNodeName(self):
        """Check the Table name getter.
        """

        name = self.table.getNodeName()
        expected = self.h5file.root.table_samples.nested_table._v_name
        self.assertEqual(name, expected, 'Unable to retrieve the Table name.')


    def test03_nodeTitle(self):
        """Check the Table title getter.
        """

        title = self.table.nodeTitle()
        expected = self.h5file.root.table_samples.nested_table._v_title
        self.assertEqual(title, expected, 'Unable to retrieve the Table title.')


    def test04_getNodePathName(self):
        """Check if the Table full path can be retrieved.
        """

        node_path = self.table.getNodePathName()
        expected = self.h5file.root.table_samples.nested_table._v_pathname
        self.assertEqual(node_path, expected, 
            'Unable to retrieve the Table full path.')


    def test05_getShape(self):
        """Check if the Table shape can be retrieved.
        """

        shape = self.table.getShape()
        expected = self.h5file.root.table_samples.nested_table.shape
        self.assertEqual(shape, expected, 
            'Unable to retrieve the Table shape.')


    def test06_tableColumnsNames(self):
        """Check if the Table column names can be retrieved.
        """

        cn = self.table.tableColumnsNames()
        expected = self.h5file.root.table_samples.nested_table.colnames
        self.assertEqual(cn, expected, 
            'Unable to retrieve the list of Table column names.')


    def test07_tableColumnsShapes(self):
        """Check if the Table column shapes can be retrieved.
        """

        cs = self.table.tableColumnsShapes()
        coldescrs = self.h5file.root.table_samples.nested_table.coldescrs
        expected = dict((k, v.shape) for (k, v) in coldescrs.iteritems())
        self.assertEqual(cs, expected, 
            'Unable to retrieve the list of Table column shapes.')


    def test08_tableColumnsTypes(self):
        """Check if the Table column types can be retrieved.
        """

        ct = self.table.tableColumnsTypes()
        expected = self.h5file.root.table_samples.nested_table.coltypes
        self.assertEqual(ct, expected, 
            'Unable to retrieve the list of Table column types.')


    def test09_numRows(self):
        """Check if the number of rows of the Table can be retrieved.
        """

        nrows = self.table.numRows()
        expected = self.h5file.root.table_samples.nested_table.nrows
        self.assertEqual(nrows, expected, 
            'Retrieved an incorrect number of rows.')


    def test10_numCols(self):
        """Check if the number of cols of the Table can be retrieved.
        """

        ncols = self.table.numCols()
        expected = len(self.h5file.root.table_samples.nested_table.colnames)
        self.assertEqual(ncols, expected, 
            'Retrieved an incorrect number of columns.')


    def test11_getFilters(self):
        """Check if the filters attribute of the Table can be retrieved.
        """

        filters = self.table.getFilters()
        expected = self.h5file.root.table_samples.nested_table.filters
        self.assertEqual(filters, expected, 
            'Cannot retrieve the filters attribute of Table.')


##    def test09_getNodeInfo(self):
##        """Check if the number of rows of the Group can be retrieved.
##        """
##
##        # Regular Group
##        a = arrayDoc.GroupDoc(self.h5file.root.table_samples, filePath, '/samples/b')
##        nrows = a.numRows()
##        expected = self.h5file.root.table_samples.nrows
##        self.assertEqual(nrows, expected, 'Bad number of rows for regular arrays.')
##
##        # Group that contains a scalar numarray
##        a = arrayDoc.GroupDoc(self.h5file.root.table_samples.sna, filePath, '/samples/sna')
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
    theSuite.addTest(unittest.makeSuite(TableDocTestCase))
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
