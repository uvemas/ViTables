import unittest
import sys
import os

import qt

class VTAppCLTestCase(unittest.TestCase):
    """Test case for the VTApp class (command line processing section).
    """
    
    def setUp(self):
        """Setup the examples directory path."""

        configDir = '%s/.vitables' % os.environ['HOME']
        if os.path.exists('%s/session' % configDir):
            os.unlink('%s/session' % configDir)
        self.examples_dir = os.path.abspath('examples')


    def tearDown(self):
        """Close any open file."""

        try:
            VTAPP.slotFileCloseAll()
        except NameError:
            # Once test_zz has been executed the tearDown has nothing to do
            pass


    def test_Ctor(self):
        """Check whether the VTApp class could be instantiated without arguments.
        """

        # No command line arguments
        self.assert_(isinstance(VTAPP, VTApp), 'Unable to instantiate VTApp with no args.')


    def test_mExistingFiles(self):
        """Check -m command line argument with existing files.

        Warning! there is no (yet) code for testing that files are opened
        with the correct mode.
        """

        file_path1 = '%s/tutorial1.h5' % self.examples_dir
        file_path2 = '%s/tutorial2.h5' % self.examples_dir
        VTAPP.processCommandLineArgs(mode='r', h5files=[file_path1, file_path2])
        dblist = VTAPP.dbManager.dbList()
        dblist.sort()
        expected = [file_path1, file_path2]
        expected.sort()
        self.assertEqual(dblist, expected,
            'Unable to open files from the command line with -m option. %s %s' % (dblist, expected))


    def test_mNonExistingFiles(self):
        """Check -m command line argument with unexisting files.
        """

        file_path = '%s/adeu.h5' % self.examples_dir
        VTAPP.processCommandLineArgs(mode='r', h5files=[file_path])
        dblist = VTAPP.dbManager.dbList()
        self.assert_(not file_path in dblist,  
            'Unable to deal with unexisting files from the command line with -m option.')


    def test_mCornerCases(self):
        """Check -m command line argument in corner cases.
        """

        # 1) try to open an already opened file
        file_path = '%s/tutorial1.h5' % self.examples_dir
        VTAPP.processCommandLineArgs(mode='r', h5files=[file_path,  file_path])
        dblist = VTAPP.dbManager.dbList()
        self.assert_(dblist.count(file_path) == 1,  
            'Unable to deal with already opened files from the command line with -m option.')

        VTAPP.slotFileCloseAll()
        # 2) try to open existing and unexisting files
        file_path1 = '%s/tutorial1.h5' % self.examples_dir
        file_path2 = '%s/adeu.h5' % self.examples_dir
        VTAPP.processCommandLineArgs(mode='r', h5files=[file_path1, file_path2])
        dblist = VTAPP.dbManager.dbList()
        expected = [file_path1]
        self.assertEqual(dblist, expected,
            'Unable to deal simultaneously with existing and unexisting files from the command line with -m option.')


    def test_dCornerCases(self):
        """Check -d command line argument in corner cases.
        
        Warning! there is no (yet) code for testing that files are opened
        with the correct mode.
        """

        # The dblist file contents follows:
        # w#@#examples/array3.h5
        # a#@#examples/array4.h5
        # r#@#examples/carray1.h5
        # x#@#examples/ctable1.h5
        # r#@#examples/earray24.h5
        # r###examples/earray25.h5

        file_path = os.path.abspath('tests/h5list.txt')
        f = VTAPP.processCommandLineArgs(dblist=file_path)
        dblist = VTAPP.dbManager.dbList()
        self.assert_(not 'examples/array3.h5' in dblist,
            'Unable to deal with bad modes from the command line with -d option.')
        self.assert_(not 'examples/ctable1.h5' in dblist,
            'Unable to deal with bad modes from the command line with -d option.')
        self.assert_(not 'examples/earray25.h5' in dblist,
            'Unable to deal with bad lines from the command line with -d option.')
        self.assert_('examples/array4.h5' in dblist,
            'Unable to deal with OK lines from the command line with -d option.')
        self.assert_('examples/carray1.h5' in dblist,
            'Unable to deal with OK lines from the command line with -d option.')
        self.assert_(not 'examples/earray24.h5' in dblist,
            'Unable to deal with unexisting files from the command line with -d option.')


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
    theSuite.addTest(unittest.makeSuite(VTAppCLTestCase))
    return theSuite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
