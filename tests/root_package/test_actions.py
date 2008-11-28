import unittest
import sys
import os

import qt

import vitables.treeEditor.treeView as treeView

class ActionsTestCase(unittest.TestCase):
    """Test case for the status of tha actions tied to menus an toolbars.
    
    The status of the actions that must remain always active is not tested.
    These actions are File-->New, File--> Open, File-->Exit, and every
    Tools and Help action. Most actions in the Windows menu are managed by Qt.
    """

    def setUp(self):
        """The filepath of the sample hdf5 file."""
        self.filepath = qt.QString(os.path.abspath('tests/samples.h5'))


    def tearDown(self):
        """Close any open file."""

        try:
            VTAPP.slotFileCloseAll()
        except NameError:
            # Once test99 has been executed the tearDown has nothing to do
            pass


    def test01_Ctor(self):
        """Check whether the VTApp class could be instantiated.
        """

        self.assert_(isinstance(VTAPP, VTApp), 
            'Unable to instantiate the VTApp class.')


    def test02_FileCloseAll(self):
        """Check whether the File --> Close All action is properly enabled (I).
        """

        VTAPP.slotFileCloseAll()
        VTAPP.slotFileOpen(self.filepath)
        self.assertEqual(VTAPP.gui.actions['fileCloseAll'].isEnabled(), True, 
            '''There is an open file, File--> Close All menu item should be'''\
            ''' enabled''')


    def test03_FileCloseAll(self):
        """Check whether the File --> Close All action is properly enabled (II).
        """

        
        self.assertEqual(VTAPP.gui.actions['fileCloseAll'].isEnabled(), False, 
            '''There are no open files, File--> Close All menu item should '''\
            '''be disabled''')


    def test04_FileClose(self):
        """Check whether the File --> Close action is properly enabled (I).
        """

        self.assertEqual(VTAPP.gui.actions['fileClose'].isEnabled(), False, 
            '''There are no open files (I), File--> Close menu item should '''\
            '''be disabled''')


    def test05_FileClose(self):
        """Check whether the File --> Close action is properly enabled (II).
        """

        VTAPP.otLV.setSelected(VTAPP.queryRoot, True)
        self.assertEqual(VTAPP.gui.actions['fileClose'].isEnabled(), False, 
            '''There are no open files (II), File--> Close menu item should'''\
            ''' be disabled''')


    def test06_FileSaveAs(self):
        """Check whether the File --> Save As... action is properly enabled (I).
        """

        VTAPP.slotFileOpen(self.filepath)
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        self.assertEqual(VTAPP.gui.actions['fileSaveAs'].isEnabled(), True, 
            '''There is a selected item, File-->Save As... menu item '''\
            '''should be enabled''')


    def test07_FileSaveAs(self):
        """Check whether the File --> Save As... action is properly enabled (II).
        """

        self.assertEqual(VTAPP.gui.actions['fileSaveAs'].isEnabled(), False, 
            '''There are no open files (I), File-->Save As... menu item '''\
            '''should be disabled''')


    def test08_FileSaveAs(self):
        """Check whether the File --> Save As... action is properly enabled (III).
        """

        VTAPP.otLV.setSelected(VTAPP.queryRoot, True)
        self.assertEqual(VTAPP.gui.actions['fileSaveAs'].isEnabled(), False, 
            '''There are no open files (II), File-->Save As... menu item '''\
            '''should be disabled''')


    def test09_NodeOpen(self):
        """Check whether the Node --> Open action is properly enabled (I).
        """

        VTAPP.slotFileOpen(self.filepath)
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        self.assertEqual(VTAPP.gui.actions['nodeOpen'].isEnabled(), False, 
            '''There are no selected leaves, Node --> Open menu item '''\
            '''should be disabled''')


    def test10_NodeOpen(self):
        """Check whether the Node --> Open action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('earray', 0)
        VTAPP.otLV.setSelected(leaf, True)
        # The selected node has no view so Node --> Open should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeOpen'].isEnabled(), True, 
            '''There is a selected leaf with no view, Node --> Open menu '''\
            '''item should be enabled''')


    def test11_NodeOpen(self):
        """Check whether the Node --> Open action is properly enabled (III).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('earray', 0)
        VTAPP.otLV.setSelected(leaf, True)
        VTAPP.slotNodeOpen()
        # The selected node has a view so Node --> Open should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeOpen'].isEnabled(), False, 
            '''There is a selected leaf, Node --> Open menu item '''\
            '''should be disabled''')


    def test12_NodeOpen(self):
        """Check whether the Node --> Open action is properly enabled (IV).
        """

        # There are not selected nodes so Node --> Open should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeOpen'].isEnabled(), False, 
            '''There are not selected nodes, Node --> Open menu item '''\
            '''should be disabled''')


    def test13_NodeClose(self):
        """Check whether the Node --> Close action is properly enabled (I).
        """

        VTAPP.slotFileOpen(self.filepath)
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        self.assertEqual(VTAPP.gui.actions['nodeClose'].isEnabled(), False, 
            '''There are no selected leaves, Node --> Close menu item '''\
            '''should be disabled''')


    def test14_NodeClose(self):
        """Check whether the Node --> Close action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('earray', 0)
        VTAPP.otLV.setSelected(leaf, True)
        # The selected node has no view so Node --> Close should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeClose'].isEnabled(), False, 
            '''There is a selected leaf with no view, Node --> Close menu '''\
            '''item should be disabled''')


    def test15_NodeClose(self):
        """Check whether the Node --> Close action is properly enabled (III).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('earray', 0)
        VTAPP.otLV.setSelected(leaf, True)
        VTAPP.slotNodeOpen()
        # The selected node has a view so Node --> Close should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeClose'].isEnabled(), True, 
            '''There is a selected leaf, Node --> Close menu item '''\
            '''should be enabled''')


    def test16_NodeClose(self):
        """Check whether the Node --> Close action is properly enabled (IV).
        """

        # There are not selected nodes so Node --> Close should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeClose'].isEnabled(), False, 
            '''There are not selected nodes, Node --> Close menu item '''\
            '''should be disabled''')


    def test17_NodeProperties(self):
        """Check whether the Node --> Properties action is properly enabled (I).
        """

        # The are no selected nodes so Node --> Properties should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeProperties'].isEnabled(), 
            False, '''There are no selected nodes, Node --> Properties menu'''\
            ''' item should be disabled''')


    def test18_NodeProperties(self):
        """Check whether the Node --> Properties action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        # A root node is selected so Node --> Properties should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeProperties'].isEnabled(), True, 
            '''A root node is selected, Node --> Properties menu item '''\
            '''should be enabled''')


    def test19_NodeProperties(self):
        """Check whether the Node --> Properties action is properly enabled (III).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # A group node is selected so Node --> Properties should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeProperties'].isEnabled(), 
            True, '''A group node is selected, Node --> Properties menu '''\
            '''item should be enabled''')


    def test20_NodeProperties(self):
        """Check whether the Node --> Properties action is properly enabled (III).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('earray', 0)
        VTAPP.otLV.setSelected(leaf, True)
        # A leaf node is selected so Node --> Properties should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeProperties'].isEnabled(), 
            True, '''A leaf node is selected, Node --> Properties menu item'''\
            ''' should be enabled''')


    def test21_NodeProperties(self):
        """Check whether the Node --> Properties action is properly enabled (IV).
        """

        # There are not selected nodes so Node --> Properties should be
        # disabled
        self.assertEqual(VTAPP.gui.actions['nodeProperties'].isEnabled(), 
            False, '''There are not selected nodes, Node --> Close menu '''\
            '''item should be disabled''')


    def test22_NodeCopy(self):
        """Check whether the Node --> Copy action is properly enabled (I).
        """

        # The are no selected nodes so Node --> Copy should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeCopy'].isEnabled(), False, 
            '''There are no selected nodes, Node --> Copy menu item '''\
            '''should be disabled''')


    def test23_NodeCopy(self):
        """Check whether the Node --> Copy action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        # A root node is selected so Node --> Copy should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeCopy'].isEnabled(), True, 
            '''A root node is selected, Node --> Copy menu item '''\
            '''should be enabled''')


    def test24_NodeCopy(self):
        """Check whether the Node --> Copy action is properly enabled (III).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # A group node is selected so Node --> Copy should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeCopy'].isEnabled(), True, 
            '''A group node is selected, Node --> Copy menu item '''\
            '''should be enabled''')


    def test25_NodeCopy(self):
        """Check whether the Node --> Copy action is properly enabled (IV).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('earray', 0)
        VTAPP.otLV.setSelected(leaf, True)
        # A leaf node is selected so Node --> Copy should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeCopy'].isEnabled(), True, 
            '''A leaf node is selected, Node --> Copy menu item '''\
            '''should be enabled''')


    def test26_NodeCopy(self):
        """Check whether the Node --> Copy action is properly enabled (V).
        """

        # There are not selected nodes so Node --> Copy should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeCopy'].isEnabled(), False, 
            '''There are not selected nodes, Node --> Copy menu item '''\
            '''should be disabled''')


    def test27_NodeNew(self):
        """Check whether the Node --> New action is properly enabled (I).
        """

        VTAPP.slotFileOpen(self.filepath, mode='r')
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Access mode is read-only so Node --> New should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeNew'].isEnabled(), False, 
            '''Access mode is read-only, Node --> New menu item '''\
            '''should be disabled''')


    def test28_NodeNew(self):
        """Check whether the Node --> New action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('earray', 0)
        VTAPP.otLV.setSelected(leaf, True)
        # Selected parent node is a leaf so Node --> New should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeNew'].isEnabled(), False, 
            '''Parent node cannot be a leaf, Node --> New menu item '''\
            '''should be disabled''')


    def test30_NodeNew(self):
        """Check whether the Node --> New action is properly enabled (IV).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Node --> New should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeNew'].isEnabled(), True, 
            '''Node --> New menu item should be enabled''')


    def test31_NodeNew(self):
        """Check whether the Node --> New action is properly enabled (V).
        """

        # There are not selected nodes so Node --> New should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeNew'].isEnabled(), False, 
            '''There are not selected nodes, Node --> New menu item '''\
            '''should be disabled''')


    def test32_NodeRename(self):
        """Check whether the Node --> Rename action is properly enabled (I).
        """

        VTAPP.slotFileOpen(self.filepath, mode='r')
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Access mode is read-only so Node --> Rename should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeRename'].isEnabled(), False, 
            '''Access mode is read-only, Node --> Rename menu item '''\
            '''should be disabled''')


    def test33_NodeRename(self):
        """Check whether the Node --> Rename action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        self.assertEqual(VTAPP.gui.actions['nodeRename'].isEnabled(), False, 
            '''Root nodes cannot be renamed, Node --> Rename menu item '''\
            '''should be disabled''')


    def test34_NodeRename(self):
        """Check whether the Node --> Rename action is properly enabled (III).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Node --> Rename should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeRename'].isEnabled(), True, 
            '''Node --> Rename menu item '''\
            '''should be enabled''')


    def test35_NodeRename(self):
        """Check whether the Node --> New action is properly enabled (V).
        """

        # There are not selected nodes so Node --> Rename should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeRename'].isEnabled(), False, 
            '''There are not selected nodes, Node --> Rename menu item '''\
            '''should be disabled''')


    def test36_NodeCut(self):
        """Check whether the Node --> Cut action is properly enabled (I).
        """

        VTAPP.slotFileOpen(self.filepath, mode='r')
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Access mode is read-only so Node --> Cut should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeCut'].isEnabled(), False, 
            '''Access mode is read-only, Node --> Cut menu item '''\
            '''should be disabled''')


    def test37_NodeCut(self):
        """Check whether the Node --> Cut action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        self.assertEqual(VTAPP.gui.actions['nodeCut'].isEnabled(), False, 
            '''Root nodes cannot be cut, Node --> Cut menu item '''\
            '''should be disabled''')


    def test38_NodeCut(self):
        """Check whether the Node --> Cut action is properly enabled (III).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Node --> Cut should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeCut'].isEnabled(), True, 
            '''Node --> Cut menu item '''\
            '''should be enabled''')


    def test39_NodeCut(self):
        """Check whether the Node --> Cut action is properly enabled (IV).
        """

        # There are not selected nodes so Node --> Cut should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeCut'].isEnabled(), False, 
            '''There are not selected nodes, Node --> Cut menu item '''\
            '''should be disabled''')


    def test40_NodePaste(self):
        """Check whether the Node --> Paste action is properly enabled (I).
        """

        VTAPP.slotFileOpen(self.filepath, mode='r')
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Access mode is read-only so Node --> Paste should be disabled
        self.assertEqual(VTAPP.gui.actions['nodePaste'].isEnabled(), False, 
            '''Access mode is read-only, Node --> Paste menu item '''\
            '''should be disabled''')


    def test41_NodePaste(self):
        """Check whether the Node --> Paste action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Nodes can be pasted under groups so Node --> Paste should be enabled
        self.assertEqual(VTAPP.gui.actions['nodePaste'].isEnabled(), True, 
            '''Nodes can be pasted under groups, Node --> Paste menu item '''\
            '''should be enabled''')


    def test42_NodePaste(self):
        """Check whether the Node --> Paste action is properly enabled (III).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('earray', 0)
        VTAPP.otLV.setSelected(leaf, True)
        # Nodes cannot be pasted under leaves so Node --> Paste should
        # be disabled
        self.assertEqual(VTAPP.gui.actions['nodePaste'].isEnabled(), False, 
            '''Nodes cannot be pasted under leaves, Node --> Paste menu '''\
            '''item should be disabled''')


    def test43_NodePaste(self):
        """Check whether the Node --> Paste action is properly enabled (IV).
        """

        # There are not selected nodes so Node --> Paste should be disabled
        self.assertEqual(VTAPP.gui.actions['nodePaste'].isEnabled(), False, 
            '''There are not selected nodes, Node --> Paste menu item '''\
            '''should be disabled''')


    def test44_NodeDelete(self):
        """Check whether the Node --> Delete action is properly enabled (I).
        """

        VTAPP.slotFileOpen(self.filepath, mode='r')
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Access mode is read-only so Node --> Delete should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeDelete'].isEnabled(), False, 
            '''Access mode is read-only, Node --> Delete menu item '''\
            '''should be disabled''')


    def test45_NodeDelete(self):
        """Check whether the Node --> Delete action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        # Opening a file automatically selects the root node of that file
        # in the tree viewer
        self.assertEqual(VTAPP.gui.actions['nodeDelete'].isEnabled(), False, 
            '''Root nodes cannot be cut, Node --> Delete menu item '''\
            '''should be disabled''')


    def test46_NodeDelete(self):
        """Check whether the Node --> Delete action is properly enabled (III).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        # Node --> Delete should be enabled
        self.assertEqual(VTAPP.gui.actions['nodeDelete'].isEnabled(), True, 
            '''Access mode is read-only, Node --> Delete menu item '''\
            '''should be enabled''')


    def test47_NodeDelete(self):
        """Check whether the Node --> Delete action is properly enabled (I).
        """

        # There are not selected nodes so Node --> Delete should be disabled
        self.assertEqual(VTAPP.gui.actions['nodeDelete'].isEnabled(), False, 
            '''There are not selected nodes, Node --> Delete menu item '''\
            '''should be disabled''')


    def test48_QueryNew(self):
        """Check whether the Query --> New action is properly enabled (I).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('array_samples', 0)
        VTAPP.otLV.setSelected(group, True)
        dbdoc = VTAPP.dbManager.getDB(self.filepath)
        node = dbdoc.getNode(group.where)
        # The selected node has no attribute 'description' so
        # Query --> New should be disabled
        self.assertEqual(VTAPP.gui.actions['queryNew'].isEnabled(), False, 
            '''The selected node has no attribute 'description', Query --> '''\
            '''New menu item should be disabled''')


    def test49_QueryNew(self):
        """Check whether the Query --> New action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('table_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('empty_table', 0)
        VTAPP.otLV.setSelected(leaf, True)
        dbdoc = VTAPP.dbManager.getDB(self.filepath)
        node = dbdoc.getNode(leaf.where)
        # The selected node has attribute 'description' so Query --> New
        # should be enabled
        self.assertEqual(VTAPP.gui.actions['queryNew'].isEnabled(), True, 
            '''The selected node has attribute 'description', Query --> '''\
            '''New menu item should be enabled''')


    def test52_QueryNew(self):
        """Check whether the Query --> New action is properly enabled (V).
        """

        # There are not selected nodes so Query --> New should be disabled
        self.assertEqual(VTAPP.gui.actions['queryNew'].isEnabled(), False, 
            '''There are not selected nodes, Query --> New menu item '''\
            '''should be disabled''')


    def test57_QueryDeleteAll(self):
        """Check whether the Query --> DeleteAll action is properly enabled (I).
        """

        tmp_dbdoc = VTAPP.dbManager.getDB(VTAPP.dbManager.tmp_filepath)
        qrootNode = tmp_dbdoc.getNode(VTAPP.queryRoot.where)
        children = qrootNode._v_nchildren
        # There are no filtered tables so Query --> Delete All should be
        # disabled
        self.assertEqual(VTAPP.gui.actions['queryDeleteAll'].isEnabled(), 
            False, '''There are no filtered tables, Query --> Delete All '''\
            '''menu item should be disabled''')


    def test58_QueryDeleteAll(self):
        """Check whether the Query --> DeleteAll action is properly enabled (II).
        """

        VTAPP.slotFileOpen(self.filepath)
        VTAPP.otLV.setOpen(VTAPP.otLV.selectedItem(), True)
        group = VTAPP.otLV.findItem('table_samples', 0)
        VTAPP.otLV.setOpen(group, True)
        leaf = VTAPP.otLV.findItem('empty_table', 0)
        VTAPP.otLV.setSelected(leaf, True)
        # Copy the table /detector/readout in the temporary database
        VTAPP.slotNodeCopy()
        VTAPP.otLV.setSelected(VTAPP.queryRoot, True)
        VTAPP.slotNodePaste()
        VTAPP.slotFileCloseAll()
        # Get the number of filtered tables
        tmp_dbdoc = VTAPP.dbManager.getDB(VTAPP.dbManager.tmp_filepath)
        qrootNode = tmp_dbdoc.getNode(VTAPP.queryRoot.where)
        children = qrootNode._v_nchildren
        # There are filtered tables so Query --> Delete All should be enabled
        self.assertEqual(VTAPP.gui.actions['queryDeleteAll'].isEnabled(), 
            True, '''There are %s filtered tables, Query --> Delete All '''\
            '''menu item should be enabled''' % children)
        # Select the Query results/readout Table and delete it
        VTAPP.otLV.setOpen(VTAPP.queryRoot, True)
        leaf = VTAPP.otLV.findItem('empty_table', 0)
        VTAPP.otLV.setSelected(leaf, True)
        VTAPP.slotNodeDelete(force=True)


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


def suite():
    """Return a test suite consisting of all the test cases in the module."""

    globalSetup()
    theSuite = unittest.TestSuite()
    theSuite.addTest(unittest.makeSuite(ActionsTestCase))
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
