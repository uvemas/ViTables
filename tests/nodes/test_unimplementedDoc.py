import unittest
import sys
import os

import tables

import qt

import vitables.nodes.unimplementedDoc as unimplementedDoc

class UnImplementedDocTestCase(unittest.TestCase):
    """Test case for the UnImplementedDoc class.
    """

    def setUp(self):
        """Open the sample hdf5 file and instantiate an UnImplementedDoc object."""

        filepath = os.path.abspath('tests/hdf5_sample.h5')
        VTAPP.dbManager.openDB(filepath, mode='a')
        doc = VTAPP.dbManager.getDB(filepath)
        nodepath = '/images/iceberg_palette'
        self.node = unimplementedDoc.UnImplementedDoc(doc, nodepath)


    def tearDown(self):
        """Close any open file."""

        try:
            VTAPP.slotFileCloseAll()
        except NameError:
            # Once test99 has been executed the tearDown has nothing to do
            pass


    def test01_unImplementedDocInstance(self):
        """Check whether the UnImplementedDoc class could be instantiated.
        """

        self.assert_(isinstance(self.node, unimplementedDoc.UnImplementedDoc), 
            'Unable to instantiate the UnImplementedDoc class.')


    def test02_getNodeInfo(self):
        """Check whether node info can be retrieved.
        """

        info = self.node.getNodeInfo()
        expected = {'type': 'UnImplemented'}
        self.assertEqual(info, expected, 'Unable to get node info.')


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
    theSuite.addTest(unittest.makeSuite(UnImplementedDocTestCase))
    return theSuite


if __name__ == '__main__':
    # ptdump output for hdf5_sample.h5
    # hdf5_sample.h5 (File) ''
    # Last modif.: 'Wed Jun 20 09:54:52 2007'
    # Object Tree:
    # / (RootGroup) ''
    # /A note (Array(2L,)) ''
    # /arrays (Group) ''
    # /arrays/2D float array (Array(100L, 50L)) ''
    # /arrays/2D int array (Array(100L, 50L)) ''
    # /arrays/3D int array (Array(100L, 50L, 10L)) ''
    # /arrays/Vdata table: PerBlockMetadataCommon (Table(153L,)) ''
    # /arrays/external (Array(10L, 5L)) ''
    # /datatypes (Group) ''
    # /images (Group) ''
    # /images/Iceberg (ImageArray(375L, 375L)) ''
    # /images/iceberg_palette (UnImplemented(256, 3)) ''
    # /images/landcover.umd.199906.jpg (ImageArray(180L, 360L, 3L)) ''
    # /images/pixel interlace (ImageArray(149L, 227L, 3L)) ''
    # /images/plane interlace (ImageArray(3L, 149L, 227L)) ''
    # /arrays/Link to arrays (Group) ''

    unittest.main(defaultTest='suite')
