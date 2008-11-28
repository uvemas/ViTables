import unittest
import sys
import os

import PyQt4.QtCore as qtCore
import PyQt4.QtGui as qtGui

class PreferencesTestCase(unittest.TestCase):
    """Test case for the Preferences class.

    Warning! the following methods remain untested:
    - slotApplyButton
    """

    def setUp(self):
        """Create an instance of the Preferences class."""
    
        # The application preferences that will be used for testing purposes
        test_config = {}
        # Startup
        test_config['Startup/lastWorkingDirectory'] = 'home'
        test_config['Startup/startupWorkingDirectory'] = 'home'
        test_config['Startup/restoreLastSession'] = 1
        # Logger
        test_config['Logger/paper'] = qtGui.QColor('white')
        test_config['Logger/text'] = qtGui.QColor('black')
        test_config['Logger/font'] = qtGui.QFont('Helvetica', 10, -1)
        # Workspace
        test_config['Workspace/background'] = qtGui.QColor('white')
        # Style
        test_config['Look/currentStyle'] = 'default'
    
        self.prefs = vtprefs.Preferences(None, test_config)
        self.prefs.gui.show()
    

    def tearDown(self):
        """Delete the instance of the Preferences class."""
        del self.prefs


    def test01_Ctor(self):
        """Check whether the Preferences class could be instantiated.
        """

        self.assert_(isinstance(self.prefs, vtprefs.Preferences), 
            'Unable to instantiate the Preferences class.')


    def test02_InitialStateSetup(self):
        """Check whether the Preferences dialog is initialised properly.
        """

        # The Preferences dialog is initialised with the current preferences
        # These settings are stored in the new_prefs attribute (a dictionary)
        config = self.prefs.new_prefs

        #
        # Check the initialisation
        #

        # Startup: radio button ID
        rbID = self.prefs.gui.hiden_bg.checkedId()
        expected = self.prefs.button2id[config['Startup/startupWorkingDirectory']]
        self.assertEqual(rbID, expected,
            'Startup working directory is not setup properly')
        # Startup: checkbox activation state
        dlg_checkbox = self.prefs.gui.restore_cb.isChecked()
        expected = config['Startup/restoreLastSession']
        self.assertEqual(dlg_checkbox, expected,
            'Restore last session is not setup properly')
        # Logger
        dlg_font = self.prefs.gui.sample_te.font()
        expected = config['Logger/font']
        self.assertEqual(dlg_font, expected,
            'Logger font is not setup properly')
        dlg_color = self.prefs.gui.sample_te.textColor()
        expected = config['Logger/text']
        self.assertEqual(dlg_color, expected,
            'Logger color is not setup properly')
        dlg_paper = self.prefs.gui.sample_te.palette().color(qtGui.QPalette.Background)
        expected = config['Logger/paper']
        self.assertEqual(dlg_paper, expected,
            'Logger paper is not setup properly')
        # Workspace
        dlg_wbg = self.prefs.gui.workspace_label.palette().color(qtGui.QPalette.Background)
        expected = config['Workspace/background']
        self.assertEqual(dlg_wbg, expected,
            'Workspace background is not setup properly')
        # Style
        dlg_style = str(self.prefs.gui.styles_cb.currentText())
        expected = config['Look/currentStyle']
        self.assertEqual(dlg_style, expected,
            'Application style is not setup properly')


    def test03_SlotDefaultButton(self):
        """Check whether the Preferences dialog is defaulted properly.
        """

        # Apply the default configuration to the Preferences dialog
        self.prefs.slotDefaultButton()

        #
        # Check that configuration is the default one
        #

        # Startup
        rbID = self.prefs.gui.hiden_bg.checkedId()
        expected = self.prefs.button2id[Config.confDef['Startup/startupWorkingDirectory']]
        self.assertEqual(rbID, expected,
            'Startup working directory is not defaulted properly')
        dlg_checkbox = self.prefs.gui.restore_cb.isChecked()
        expected = Config.confDef['Startup/restoreLastSession']
        self.assertEqual(dlg_checkbox, expected,
            'Restore last session is not setup properly')
        # Logger
        dlg_font = self.prefs.gui.sample_te.font()
        expected = Config.confDef['Logger/font']
        self.assertEqual(dlg_font, expected,
            'Logger font is not setup properly')
        dlg_color = self.prefs.gui.sample_te.textColor()
        expected = qtGui.QColor(Config.confDef['Logger/text'])
        self.assertEqual(dlg_color, expected,
            'Logger color is not setup properly')
        dlg_paper = self.prefs.gui.sample_te.palette().color(qtGui.QPalette.Background)
        expected = qtGui.QBrush(qtGui.QColor(Config.confDef['Logger/paper']))
        self.assertEqual(dlg_paper, expected,
            'Logger paper is not setup properly')
        # Workspace
        dlg_wbg = self.prefs.gui.workspace_label.palette().color(qtGui.QPalette.Background)
        expected = qtGui.QColor(Config.confDef['Workspace/background'])
        self.assertEqual(dlg_wbg, expected,
            'Workspace background is not setup properly')
        # Style
        dlg_style = str(self.prefs.gui.styles_cb.currentText())
        expected = Config.confDef['Look/currentStyle']
        self.assertEqual(dlg_style, expected,
            'Application style is not setup properly')


    def test04_SlotSetStartupDir(self):
        """Check whether the working directory is setup properly.
        """

        # Setup the startup working directory to home
        self.prefs.slotSetStartupDir(1)
        expected = 'home'
        self.assertEqual(self.prefs.new_prefs['Startup/startupWorkingDirectory'], 
            expected, 'Startup working directory is not setup properly')


    def test05_SlotSetStartupSession(self):
        """Check whether the recover last session is setup properly.
        """

        # Setup the restore session at startup to True
        self.prefs.slotSetStartupSession(1)
        expected = 1
        self.assertEqual(self.prefs.new_prefs['Startup/restoreLastSession'], 
            expected, 'Recover last session is not setup properly')


    def test06_SlotSetLoggerFont(self):
        """Check whether the logger font is setup properly.
        """

        self.prefs.slotSetLoggerFont()
        expected = self.prefs.gui.sample_te.font()
        self.assertEqual(self.prefs.new_prefs['Logger/font'], expected,
            'Logger font is not setup properly')


    def test07_SlotSetLoggerForeground(self):
        """Check whether the logger text color is setup properly.
        """

        self.prefs.slotSetLoggerForeground()
        expected = self.prefs.gui.sample_te.textColor()
        self.assertEqual(self.prefs.new_prefs['Logger/text'], expected,
            'Logger text color is not setup properly')


    def test08_SlotSetLoggerBackground(self):
        """Check whether the logger paper is setup properly.
        """

        self.prefs.slotSetLoggerBackground()
        expected = self.prefs.gui.sample_te.palette().color(qtGui.QPalette.Background)
        self.assertEqual(self.prefs.new_prefs['Logger/paper'], expected,
            'Logger paper is not setup properly')


    def test09_SlotSetWorkspaceBackground(self):
        """Check whether the workspace background is setup properly.
        """

        self.prefs.slotSetWorkspaceBackground()
        expected = self.prefs.gui.workspace_label.palette().color(qtGui.QPalette.Background)
        self.assertEqual(self.prefs.new_prefs['Workspace/background'], expected,
            'Workspace background is not setup properly')


    def test10_SlotSetStyle(self):
        """Check whether the style is setup properly.
        """

        self.prefs.slotSetStyle(qtCore.QString('SGI'))
        expected = 'SGI'
        self.assertEqual(self.prefs.new_prefs['Look/currentStyle'], expected,
            'Style is not setup properly')


    def test99_applyDefaults(self):
        """Apply default settings before exiting the unittest.
        """

        # Apply the default configuration to the Preferences dialog
        self.prefs.slotDefaultButton()


def globalSetup():
    global QTAPP, vtprefs, Config

    # Avoid <QApplication: There should be max one application object> errors:
    # if an instance of QApplication already exists then use a pointer to it
    QTAPP = qtGui.qApp
    if QTAPP.type() != 1:
        QTAPP = qtGui.QApplication(sys.argv)
    import vitables.preferences.preferences as vtprefs
    from vitables.preferences.vtconfig import Config


def suite():
    """Return a test suite consisting of all the test cases in the module."""

    globalSetup()
    theSuite = unittest.TestSuite()
    theSuite.addTest(unittest.makeSuite(PreferencesTestCase))
    return theSuite


if __name__ == '__main__':
    unittest.main(defaultTest='suite' )


