import unittest
import sys
import os

import PyQt4.QtCore as qtCore
import PyQt4.QtGui as qtGui

import vitables.vtSite as vtSite

class ConfigTestCase(unittest.TestCase):
    """Test case for the Config class.

    This method assumes that a configuration file $HOME/.vitables/Carabos/vitables.conf
    exists.
    Warning: I don't know how to check the dictionary of default values.
    """

    def setUp(self):
        """Create an instance of the Config class."""
        self.config = vtconfig.Config()


    def tearDown(self):
        """Delete the instance of the Config class."""
        del self.config


    def test01_Ctor(self):
        """Check whether the Config class could be instantiated.
        """

        self.assert_(isinstance(self.config, vtconfig.Config), 
            'Unable to instantiate the Config class.')


    def test02_Version(self):
        """Check the version number.
        """

        # The vtSite module should provide the version number
        expected = vtSite.VERSION
        self.assert_(vtconfig.getVersion() == expected, 'Bad version number')


    def test03_DataDir(self):
        """Check the data directory.
        """

        # The vtSite module should provide the data directory
        expected = vtSite.DATADIR
        self.assert_(self.config.data_directory == expected,
            'Bad data directory path.')


    def test04_TranslationsDir(self):
        """Check the translations directory.
        """

        # The vtSite module should provide the data directory where
        # the translations directory lives
        data_dir = vtSite.DATADIR
        expected = os.path.join(data_dir,'translations')
        self.assert_(self.config.translations_dir == expected,
            'Bad translations directory path.')


    def test05_IconsDir(self):
        """Check the icons directory.
        """

        # The vtSite module should provide the data directory where
        # the icons directory lives
        data_dir = vtSite.DATADIR
        expected = os.path.join(data_dir,'icons')
        self.assert_(self.config.icons_dir == expected, 'Bad icons directory path.')


    def test06_DocDir(self):
        """Check the doc directory.
        """

        # The vtSite module should provide the data directory where
        # the documentation directory lives
        data_dir = vtSite.DATADIR
        expected = os.path.join(data_dir,'doc')
        self.assert_(self.config.doc_dir == expected,
            'Bad documentation directory path.')


    def test07_DefaultStartupStyle(self):
        """Check the default startup style.
        """

        # The default style depends on the platform
        if sys.platform.startswith('win'):
            # if VER_PLATFORM_WIN32_NT (i.e WindowsNT/2000/XP)
            if sys.getwindowsversion()[3] == 2:
                expected = 'WindowsXP'
                self.assert_(self.config.default_style == expected,
                    'Bad default style for Windows NT platforms.')
            else:
                expected = 'Windows'
                self.assert_(self.config.default_style == expected,
                    'Bad default style for Windows (not NT) platforms.')
        elif sys.platform.startswith('darwin'):
            expected = 'Macintosh (Aqua)'
            self.assert_(self.config.default_style == expected,
                'Bad default style for Mac OS X platforms.')
        else:
            expected = 'Motif'
            self.assert_(self.config.default_style == expected,
                'Bad default style for Unix platforms.')


    def test08_ApplicationSettings(self):
        """Check the availability of the application settings.
        """

        # The application configuration will be stored in a plain text
        # file or in the Windows registry
        if sys.platform.startswith('win'):
            # On windows systems settings will be stored in the registry
            # under the Carabos key
            key = _winreg.HKEY_LOCAL_MACHINE
            subkey = 'SOFTWARE\Carabos\ViTables'
            try:
                key_handle = _winreg.OpenKey(key, subkey)
            except WindowsError:
                key_handle = False
            self.assert_(key_handle,
                'The ViTables key cannot be found in the registry')
        elif sys.platform.startswith('darwin'):
            # Mac OS X saves settings in a properties list stored in a
            # standard location (either on a global or user basis).
            # QSettings will create the appropriate plist file com.ViTables.plist
            config_path = os.path.join(str(qtCore.QDir.homePath()),
                'Library/Preferences/com.carabos.ViTables.plist')
            self.assert_(os.path.isfile(config_path),
                'The configuration plist com.carabos.ViTables.plist cannot be found.')
        else:
            # On Unix systems settings will be stored in a plain text
            # file (see the module docstring for name conventions)
            config_path = os.path.join(str(qtCore.QDir.homePath()),
                '.vitables/Carabos/ViTables.conf')
            self.assert_(os.path.isfile(config_path),
                'The configuration file ViTables.conf cannot be found.')


    def test09_WriteProperty(self):
        """Check the setter method for property values.
        """

        # A test configuration file with random values is created
        # Write Window Position
        wp = [10, 10, 650, 450]
        self.config.writeProperty('Geometry/position', wp)
        # Write HSplitter Sizes
        hss = [50, 600]
        self.config.writeProperty('Geometry/hsplitter', hss)
        # Write VSplitter Sizes
        vss = [400, 50]
        self.config.writeProperty('Geometry/vsplitter', vss)
        # Write Logger Paper
        lp = qtGui.QBrush(qtGui.QColor('green'))
        self.config.writeProperty('Logger/paper', lp)
        # Write Logger Text Color
        ltc = qtGui.QColor('blue')
        self.config.writeProperty('Logger/text', ltc)
        # Write Logger Text Font
        ltf = qtGui.QFont('Helvetica', 10, -1)
        self.config.writeProperty('Logger/font', ltf)
        # Write Workspace Background
        wbg = qtGui.QColor('yellow')
        self.config.writeProperty('Workspace/background', wbg)
        # Write Style
        style = 'Motif'
        self.config.writeProperty('Look/currentStyle', style)
        # Write Last Working Directory
        lwd = 'home'
        self.config.writeProperty('Startup/lastWorkingDirectory', lwd)
        # Write Startup Working Directory
        swd = 'last'
        self.config.writeProperty('Startup/startupWorkingDirectory', swd)
        # Write Restore Last Session
        rls = 1
        self.config.writeProperty('Startup/restoreLastSession', rls)
        # Write Recent files
        recent = ['a#@#%s' % os.path.abspath('../samples.h5')]
        self.config.writeProperty('Recent/files', recent)
        # Write Session files
        session = ['%s#@#a#@#/path/to/node1#@#/path/to/node2' % os.path.abspath('../samples.h5'),
            '%s#@#r' % os.path.abspath('../samples.h5')]
        self.config.writeProperty('Session/files', session)
        # Write help browser history
        history = ['/path/to/file1/#ID', '/path/to/file2']
        self.config.writeProperty('/HelpBrowser/history', history)
        # Write help browser bookmarks
        bookmarks = ['/path/to/file1/#ID', '/path/to/file2']
        self.config.writeProperty('/HelpBrowser/bookmarks', bookmarks)


    def test10_ReadWindowPosition(self):
        """Check the getter method of window positions.
        """

        # Read the Geometry/position key from the test configuration file
        expected = [10, 10, 650, 450]
        self.assert_(self.config.readWindowPosition() == expected,
            "readWindowPosition() method doesn't work.")


    def test11_ReadHSplitterSizes(self):
        """Check the getter method of horizontal splitter sizes.
        """

        # Read the Geometry/hsplitter key from the test configuration file
        expected = [50, 600]
        self.assert_(self.config.readHSplitterSizes() == expected,
            "readHSplitterSizes() doesn't work.")


    def test12_ReadVSplitterSizes(self):
        """Check the getter method of vertical splitter sizes.
        """

        # Read the Geometry/vsplitter key from the test configuration file
        expected = [400, 50]
        self.assert_(self.config.readVSplitterSizes() == expected,
            "readVSplitterSizes() doesn't work")


    def test13_ReadLoggerPaper(self):
        """Check the getter method for logger paper.
        """

        # Read the Logger/paper key from the test configuration file
        paper = self.config.readLoggerPaper()
        self.assert_(isinstance(paper, qtGui.QColor),
            'readLoggerPaper() method should return a QColor instance')
        bg = str(paper.name())
        expected = '#008000'
        self.assert_(bg == expected,
            'The logger paper should be green.')


    def test14_ReadLoggerText(self):
        """Check the getter method for logger text color.
        """

        # Read the Logger/text key from the test configuration file
        fg = self.config.readLoggerText()
        self.assert_(isinstance(fg, qtGui.QColor),
            'readLoggerText() method should return a QColor instance')
        expected = '#0000ff'
        self.assert_(str(fg.name()) == expected,
            'The logger text should be blue.')


    def test15_ReadLoggerFont(self):
        """Check the getter method for logger text font.
        """

        # Read the Logger/font key from the test configuration file
        f1 = self.config.readLoggerFont()
        self.assert_(isinstance(f1, qtGui.QFont),
            'readFont() method should return a QFont instance')
        expected = qtGui.QFont('Helvetica', 10, -1)
        self.assert_(f1 == expected,
            'The font should be Helvetica, 10 points, weight normal, non italic.')


    def test16_ReadWorkspaceBackground(self):
        """Check the getter method of workspace background color.
        """

        # Read the Workspace/background key from the test configuration file
        bg = self.config.readWorkspaceBackground()
        self.assert_(isinstance(bg, qtGui.QColor),
            'readWorkspaceBackground() method should return a QColor instance')
        expected = '#ffff00'
        self.assert_(str(bg.name()) == expected,
            'readWorkspaceBackground() method should return a yelow color')


    def test17_ReadStyle(self):
        """Check the getter method of style values.
        """

        # Read the Look/customStyle key from the test configuration file
        expected = 'Motif'
        self.assert_(self.config.readStyle() == expected,
            "readStyle() method doesn't work")


    def test18_ReadLastWorkingDir(self):
        """Check the getter method of last working directory values.
        """

        # Read the Startup/lastWorkingDirectory key from the test
        # configuration file
        expected = 'home'
        self.assert_(self.config.readLastWorkingDir() == expected,
            "readLastWorkingDir() method doesn't work")


    def test18b_ReadStartupWorkingDir(self):
        """Check the getter method of startup working directory values.
        """

        # Read the Startup/startupWorkingDirectory key from the test
        # configuration file
        expected = 'last'
        self.assert_(self.config.readStartupWorkingDir() == expected,
            "readStartupWorkingDir() method doesn't work")


    def test19_ReadRestoreLastSession(self):
        """Check the getter method of restore last session values.
        """

        # Read the Startup/restoreLastSession key from the test
        # configuration file
        expected = 1
        self.assert_(self.config.readRestoreLastSession() == expected,
            "readRestoreLastSession() method doesn't work")


    def test20_ReadRecentFiles(self):
        """Check the getter method of the list of recent files.
        """

        # Read the Read/files key from the test configuration file
        expected = ['a#@#%s' % os.path.abspath('../samples.h5')]
        self.assert_(self.config.readRecentFiles() == expected,
            "readRecentFiles() method doesn't work")


    def test21_ReadSessionFiles(self):
        """Check the getter method of the list of recent files.
        """

        # Read the Session/files key from the test configuration file
        expected = ['%s#@#a#@#/path/to/node1#@#/path/to/node2' % os.path.abspath('../samples.h5'),
            '%s#@#r' % os.path.abspath('../samples.h5')]
        self.assert_(self.config.readSessionFiles() == expected,
            "readSessionFiles() method doesn't work")


    def test22_ReadHelpBrowserHistory(self):
        """Check the getter method of the Help Browser history.
        """

        # Read the HelpBrowser/history key from the test configuration file
        expected = ['/path/to/file1/#ID', '/path/to/file2']
        self.assert_(self.config.readHelpBrowserHistory() == expected,
            "readHelpBrowserHistory() method doesn't work")


    def test23_ReadHelpBrowserBookmarks(self):
        """Check the getter method of the Help Browser bookmarks.
        """

        # Read the HelpBrowser/bookmarks key from the test configuration file
        expected = ['/path/to/file1/#ID', '/path/to/file2']
        self.assert_(self.config.readHelpBrowserBookmarks() == expected,
            "readHelpBrowserBookmarks() method doesn't work")


    def test24_ConfigurationDefaults(self):
        """Check the keys of the dictionary of default values.
        """

        # Don't check default values (which were chosen arbitrarely), just keys
        expected = [\
            'Geometry/hsplitter', 'Geometry/position', 'Geometry/vsplitter', 
            'HelpBrowser/bookmarks', 'HelpBrowser/history', 
            'Logger/font', 'Logger/paper', 'Logger/text',
            'Look/currentStyle', 
            'Recent/files', 
            'Session/files',
            'Startup/lastWorkingDirectory', 'Startup/restoreLastSession', 
            'Startup/startupWorkingDirectory',
            'Workspace/background']
        read = vtconfig.Config.confDef.keys()
        read.sort()
        self.assert_(read == expected,
            "Default configuration dictionary error: unexpected keys")


def globalSetup():
    global QTAPP, vtconfig

    if sys.platform.startswith('win'):
        import _winreg

    # Avoid <QApplication: There should be max one application object> errors:
    # if an instance of QApplication already exists then use a pointer to it
    QTAPP = qtGui.qApp
    if QTAPP.type() != 1:
        QTAPP = qtGui.QApplication(sys.argv)
    import vitables.preferences.vtconfig as vtconfig


def suite():
    """Return a test suite consisting of all the test cases in the module."""

    globalSetup()
    theSuite = unittest.TestSuite()
    theSuite.addTest(unittest.makeSuite(ConfigTestCase))
    return theSuite


if __name__ == '__main__':
    unittest.main(defaultTest='suite' )


