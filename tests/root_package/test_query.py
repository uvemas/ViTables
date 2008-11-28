import unittest
import sys
import os
import sets

import qt

import vitables.nodes.leavesManager as leaves_manager
import vitables.vtWidgets.queryDlg as queryDlg

class QueryTestCase(unittest.TestCase):
    """Test case for the query of Table nodes.
    """

    def setUp(self):
        """Setup the examples directory path."""
        self.filepath = qt.QString(os.path.abspath('tests/samples.h5'))


    def tearDown(self):
        """Close any open file."""

        try:
            VTAPP.slotFileCloseAll()
        except NameError:
            # Once test_zz has been executed the tearDown has nothing to do
            pass


    def test_QueryEmptyTable(self):
        """Check that querying an empty table returns None.
        """

        VTAPP.slotFileCloseAll()
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        # Select /table_samples/empty_table
        group = VTAPP.otLV.findItem('table_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        table = VTAPP.otLV.findItem('empty_table', 0)
        VTAPP.otLV.setSelected(table, True)
        # Query the selected empty table
        dbdoc = VTAPP.dbManager.getDB(table.getFilepath())
        leafdoc = VTAPP.leavesManager.createLeafDoc(dbdoc, table.where)
        tmp_dbdoc = VTAPP.dbManager.getDB(VTAPP.dbManager.tmp_filepath)
        tmp_h5file = tmp_dbdoc.getH5File()
        name,  nrows = VTAPP.leavesManager.queryTable(leafdoc, tmp_h5file)
        self.assertEqual((name, nrows), (None, None), 
            """Querying an empty table should return (None,  None)""")


    def test_GetTableInfo(self):
        """Check the dictionary with information about the table being queried.
        """

        VTAPP.slotFileCloseAll()
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        # Select /table_samples/nested_table
        group = VTAPP.otLV.findItem('table_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        table = VTAPP.otLV.findItem('nested_table', 0)
        VTAPP.otLV.setSelected(table, True)
        # Get the info dictionary of the table
        dbdoc = VTAPP.dbManager.getDB(table.getFilepath())
        leafdoc = VTAPP.leavesManager.createLeafDoc(dbdoc, table.where)
        source_table = leafdoc.node
        info = leaves_manager.setInfoDictionary(source_table)
        # The expected info dictionary
        expected_info = {}
        expected_info['nrows'] = source_table.nrows
        expected_info['src_filepath'] = source_table._v_file.filename
        expected_info['src_path'] = source_table._v_pathname
        expected_info['name'] = source_table._v_name
        expected_info['col_names'] = sets.Set(source_table.colnames)
        expected_info['col_shapes'] = \
            dict((k, v.shape) for (k, v) in source_table.coldescrs.iteritems())
        expected_info['col_types'] = source_table.coltypes
        expected_info['condvars'] = {}
        expected_info['valid_fields'] = []
        # Compares with the expected dictionary
        bad_value = None
        for k in expected_info.keys():
            if info[k] != expected_info[k]:
                bad_value = k
                break
        self.assertEqual(bad_value, None, 
            """There is a problem with the %s key""" % bad_value)


    def test_SearchableFields(self):
        """Check that searchable fields are properly selected.
        """

        VTAPP.slotFileCloseAll()
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        # Select /table_samples/nested_table
        group = VTAPP.otLV.findItem('table_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        table = VTAPP.otLV.findItem('nested_table', 0)
        VTAPP.otLV.setSelected(table, True)
        # Get the info dictionary of the table
        dbdoc = VTAPP.dbManager.getDB(table.getFilepath())
        leafdoc = VTAPP.leavesManager.createLeafDoc(dbdoc, table.where)
        source_table = leafdoc.node
        info = leaves_manager.setInfoDictionary(source_table)
        # Find the searchable fields
        leaves_manager.setSearchableFields(source_table, info)
        # Compares searchable fields with the expected value
        expected_sfields = sets.Set(['ID',  'col0 (long ID)'])
        self.assertEqual(info['valid_fields'], expected_sfields, 
            """The only searchable field should be %s""" % expected_sfields)
        # Inspect the condition variables
        expected_condvars = source_table.cols._f_col('long ID')
        expected_condvars_keys = ['col0']
        self.assertEqual(info['condvars'].keys(), expected_condvars_keys, 
            """The only condvar name should be %s""" % expected_condvars_keys)
        self.assertEqual(info['condvars']['col0'], expected_condvars, 
        """The only condvar should be %s""" % expected_condvars)


    def test_InitialCondition(self):
        """Check that the initial condition (if any) is correctly set.
        """

        VTAPP.slotFileCloseAll()
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        # Select /table_samples/nested_table
        group = VTAPP.otLV.findItem('table_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        table = VTAPP.otLV.findItem('nested_table', 0)
        VTAPP.otLV.setSelected(table, True)
        # Get the info dictionary of the table
        dbdoc = VTAPP.dbManager.getDB(table.getFilepath())
        leafdoc = VTAPP.leavesManager.createLeafDoc(dbdoc, table.where)
        source_table = leafdoc.node
        info = leaves_manager.setInfoDictionary(source_table)
        leaves_manager.setSearchableFields(source_table, info)
        # Set the initial condition
        initial_cond = leaves_manager.setInitialCondition(\
            VTAPP.leavesManager.last_query_info, info)
        # Compare with the expected initial condition
        expected_value = ''
        self.assertEqual(initial_cond, expected_value, 
            """The initial condition should be empty""")


    def test_QueryComponents(self):
        """Check that the query dialog works fine.
        """

        VTAPP.slotFileCloseAll()
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        # Select /table_samples/nested_table
        group = VTAPP.otLV.findItem('table_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        table = VTAPP.otLV.findItem('nested_table', 0)
        VTAPP.otLV.setSelected(table, True)
        # Get the info dictionary of the table
        dbdoc = VTAPP.dbManager.getDB(table.getFilepath())
        leafdoc = VTAPP.leavesManager.createLeafDoc(dbdoc, table.where)
        source_table = leafdoc.node
        info = leaves_manager.setInfoDictionary(source_table)
        leaves_manager.setSearchableFields(source_table, info)
        # Set the initial condition
        initial_cond = leaves_manager.setInitialCondition(\
            VTAPP.leavesManager.last_query_info, info)
        # Launch the query dialog
        VTAPP.leavesManager.query_info = {}
        qdlg = queryDlg.QueryDlg(VTAPP.leavesManager.query_info, info, [], 0, 
            initial_cond, source_table)
        # The right thing would be something like
#        qdlg.query_le.setText('query line edit content')
#        qdlg.name_le.setText('name line edit content')
#        qdlg.indices_column.setText('my_indices')
#        qdlg.rstart.setValue(1)
#        qdlg.rstop.setValue(10)
#        qdlg.rstep.setValue(2)
#        qdlg.slotAccept()
        # Unfortunately it doesn''t work. I think it is due to the fact that we
        # do not enter the main execution loop of ViTables. As a consequence we
        # have to do
        qdlg.query_info['condition'] = 'query line edit content'
        qdlg.query_info['ft_name'] = 'name line edit content'
        qdlg.query_info['indices_field_name'] = 'my_indices'
        qdlg.query_info['rows_range'] = (0, 10, 2)
        del qdlg
        # Compare values
        expected_info = {}
        expected_info['condition'] = 'query line edit content'
        expected_info['ft_name'] = 'name line edit content'
        expected_info['indices_field_name'] = 'my_indices'
        expected_info['rows_range'] = (0, 10, 2)
        recovered_query_info = VTAPP.leavesManager.getQueryInfo()
        self.assertEqual(VTAPP.leavesManager.query_info, expected_info, 
        """The expected query info is not what expected. %s %s""" % (expected_info, recovered_query_info))


#    def test_EmptyCondition(self):
#        """Check what happens if no condition is returned.
#        """
#        raise NotImplementedError
#
#
#    def test_FilteredTableTitle(self):
#        """Check that title of the filtered table is properly set.
#
#        """
#        raise NotImplementedError
#
#
#    def test_Counter(self):
#        """Check that the queries counter is properly updated.
#
#        """
#        raise NotImplementedError
#
#
#    def test_QueryResult(self):
#        """Check the result returned by a table query.
#
#        """
#        raise NotImplementedError


    def test_zz(self):
        """Exit ViTables.

        Warning!
        The other methods are not named testNN_something so if we name
        this method test99 it will NOT be called last and errors will happen.
        """

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


def suite():
    """Return a test suite consisting of all the test cases in the module."""

    globalSetup()
    theSuite = unittest.TestSuite()
    theSuite.addTest(unittest.makeSuite(QueryTestCase))
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
