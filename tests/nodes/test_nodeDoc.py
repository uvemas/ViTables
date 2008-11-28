import unittest
import sys
import os

import tables

import qt

import vitables.nodes.nodeDoc as nodeDoc

class NodeDocTestCase(unittest.TestCase):
    """Test case for the NodeDoc class.
    """

    def setUp(self):
        """Open the sample hdf5 file and instantiate a NodeDoc object."""

        filepath = os.path.abspath('tests/samples.h5')
        VTAPP.dbManager.openDB(filepath, mode='a')
        doc = VTAPP.dbManager.getDB(filepath)
        self.h5file = doc.getH5File()
        nodepath = '/array_samples'
        self.node = nodeDoc.NodeDoc(doc, nodepath)


    def tearDown(self):
        """Close any open file."""

        try:
            VTAPP.slotFileCloseAll()
        except NameError:
            # Once test99 has been executed the tearDown has nothing to do
            pass


    def test01_nodeDocInstance(self):
        """Check whether the NodeDoc class could be instantiated.
        """
        self.assert_(isinstance(self.node, nodeDoc.NodeDoc), 
            'Unable to instantiate the NodeDoc class.')


    def test02_isInstanceOf(self):
        """Check the class of the node tied to the NodeDoc instance.
        """
        
        f = self.node.isInstanceOf('Group')
        expected = True
        self.assertEqual(f, expected, 
            'NodeDoc.isInstanceOf returns a bad value.')


    def test03_getASI(self):
        """Check if the Attribute Set Instance of the node can be retrieved.
        """

        asi = self.node.getASI()
        expected = self.h5file.root.array_samples._v_attrs
        self.assertEqual(asi, expected, 
            'Attribute Set Instance cannot be retrieved. %s %s' % \
            (asi,  expected))


    def test04_getSystemAttributesNames(self):
        """Check if the system attributes names of the node can be retrieved.
        """

        asi = self.h5file.root.array_samples._v_attrs
        # Check attribute names
        sysattr = self.node.getNodeAttributes('system')
        names = sysattr.keys()
        names.sort()
        expected = asi._v_attrnamessys
        expected.sort()
        self.assertEqual(names, expected, 
            'The list of names of system attributes cannot be retrieved.')

        # Check attribute values
        for name in names:
            value = sysattr[name]
            expected = getattr(asi, name)
            self.assertEqual(value, expected, 
                'The system attributes cannot be retrieved')


    def test05_getUserAttributesNames(self):
        """Check if the user attributes names of the node can be retrieved.
        """

        # Create a user attribute
        asi = self.h5file.root.array_samples._v_attrs
        # Check attribute names
        userattr = self.node.getNodeAttributes('user')
        names = userattr.keys()
        names.sort()
        expected = asi._v_attrnamesuser
        expected.sort()
        self.assertEqual(names, expected, 
            'The list of names of user attributes cannot be retrieved.')

        # Check attribute values
        for name in names:
            value = userattr[name]
            expected = getattr(asi, name)
            self.assertEqual(value, expected, 
                'The user attributes cannot be retrieved')


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
    theSuite.addTest(unittest.makeSuite(NodeDocTestCase))
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
