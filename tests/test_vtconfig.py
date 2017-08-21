"""Test class for vtconfig.py"""

import sys

import pytest

from qtpy import QtWidgets
# from qtpy import QtCore
from qtpy import QtGui
# from qtpy.QtTest import QTest

import vitables.utils

@pytest.mark.usefixtures('launcher')
class TestLogger(object):
    @pytest.fixture()
    def config(self, launcher):
        cfg = launcher.vtapp_object.config
        yield cfg
        # Tear down code
        cfg.writeValue('Logger/Paper', QtGui.QColor("#ffffff"))
        cfg.writeValue('Logger/Text', QtGui.QColor("#000000"))
        cfg.writeValue('Logger/Font', QtWidgets.qApp.font())
        cfg.writeValue('Workspace/Background',
                       QtGui.QBrush(QtGui.QColor("#ffffff")))
        cfg.writeValue('Look/currentStyle', cfg.default_style)
        launcher.gui.setGeometry(100, 50, 700, 500)
        cfg.writeValue('Geometry/Position', launcher.gui.saveGeometry())
        launcher.gui.logger_dock.setFloating(False)
        launcher.gui.logger_dock.setVisible(True)
        launcher.gui.file_toolbar.setVisible(True)
        cfg.writeValue('Geometry/Layout', launcher.gui.saveState())
        cfg.writeValue('Geometry/HSplitter', launcher.gui.hsplitter.saveState())
        cfg.writeValue('Session/restoreLastSession', False)
        cfg.writeValue('Session/startupWorkingDir', 'home')
        cfg.writeValue('Session/lastWorkingDir', vitables.utils.getHomeDir())

    def test_credentials(self, launcher, config):
        organization = launcher.app.organizationName()
        product = launcher.app.applicationName()
        version = launcher.app.applicationVersion()
        reg_path = 'HKEY_CURRENT_USER\\Software\\{0}\\{1}'.format(product,
                                                                  version)

        if sys.platform.startswith('win'):
            assert config.organizationName() == product
            assert config.applicationName() == version
            assert config.reg_path == reg_path
        elif sys.platform.startswith('darwin'):
            assert config.organizationName() == product
            assert config.applicationName() == version
        else:
            assert config.organizationName() == organization
            assert config.applicationName() == '-'.join((product, version))

    def test_logger(self, config):
        # Background
        bg = QtGui.QColor('#aabbcc')
        config.writeValue('Logger/Paper', bg)
        assert config.loggerPaper() == bg
        # Foreground
        fg = QtGui.QColor('#ccbbaa')
        config.writeValue('Logger/Text', fg)
        assert config.loggerText() == fg
        # Font
        font = QtGui.QFont('Times New Roman')
        config.writeValue('Logger/Font', font)
        assert config.loggerFont() == font

    def test_workspace(self, config):
        bg = QtGui.QBrush(QtGui.QColor('#aabbcc'))
        config.writeValue('Workspace/Background', bg)
        assert config.workspaceBackground() == bg

    def test_appStyle(self, config):
        style = QtWidgets.QStyleFactory.keys()[-1]
        config.writeValue('Look/CurrentStyle', style)
        assert config.readStyle() == style

    def test_windowGeometry(self, launcher, config):
        # Test the main window position and size (without the window frame)
        # Position means x and y coordinates of the top left corner
        # Size means width and height of the window
        launcher.gui.setGeometry(100, 50, 300, 250)
        config.writeValue('Geometry/Position', launcher.gui.saveGeometry())
        launcher.gui.setGeometry(150, 150, 300, 250)
        assert launcher.gui.restoreGeometry(config.windowPosition())
        assert launcher.gui.geometry().x() == 100
        assert launcher.gui.geometry().y() == 50
        assert launcher.gui.width() == 300
        assert launcher.gui.height() == 250

    def test_dockwidgetState(self, launcher, config):
        # Test the state of the main window's dockwidget
        logger_dock = launcher.gui.logger_dock
        logger_dock.setFloating(True)
        logger_dock.setVisible(False)
        config.writeValue('Geometry/Layout', launcher.gui.saveState())
        logger_dock.setFloating(False)
        assert launcher.gui.restoreState(config.windowLayout())
        assert logger_dock.isFloating()

    def test_toolbarsState(self, launcher, config):
        # Test the state (visibility and position) of the main window's toolbars
        # Note: it seems that position is not saved with saveState()
        ftb = launcher.gui.file_toolbar
        ftb.setVisible(False)
        config.writeValue('Geometry/Layout', launcher.gui.saveState())
        ftb.setVisible(True)
        assert launcher.gui.restoreState(config.windowLayout())
        assert not launcher.gui.file_toolbar.isVisible()

    def test_hsplitterState(self, launcher, config):
        launcher.gui.show()
        launcher.gui.setGeometry(100, 550, 700, 500)
        # Test the state (i.e. sizes) of the splitter
        splitter = launcher.gui.hsplitter
        expected_sizes = splitter.sizes()
        config.writeValue('Geometry/HSplitter', splitter.saveState())
        splitter.setSizes([200, 90])
        assert splitter.restoreState(config.hsplitterPosition())
        assert splitter.sizes() == expected_sizes
        launcher.gui.hide()

    def test_restoreLastSession(self, config):
        config.writeValue('Session/restoreLastSession', True)
        assert config.restoreLastSession()
        # None cannot be converted to a boolean value
        config.writeValue('Session/restoreLastSession', None)
        assert not config.restoreLastSession()

    def test_startupWorkingDir(self, config):
        config.writeValue('Session/startupWorkingDir', 'somepath')
        assert config.startupWorkingDir() == 'home'
        config.writeValue('Session/startupWorkingDir', 'last')
        assert config.startupWorkingDir() == 'last'

    def test_lastWorkingDir(self, config):
        config.writeValue('Session/lastWorkingDir', 1)
        assert config.lastWorkingDir() == vitables.utils.getHomeDir()
