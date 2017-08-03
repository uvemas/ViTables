"""Test class for vtgui.py"""

import pytest

from qtpy import QtCore
from qtpy import QtWidgets

import vitables.logger as logger


@pytest.mark.usefixtures('launcher')
class TestVTGui(object):
    def test_dockWidget(self, launcher):
        logger_dock = launcher.gui.findChild(QtWidgets.QDockWidget,
                                             'LoggerDockWidget')
        # Does the dock widget exist?
        assert logger_dock
        # Is it docked to the proper area?
        assert (launcher.gui.dockWidgetArea(logger_dock) ==
                QtCore.Qt.BottomDockWidgetArea)
        # Does it have the required features?
        assert (logger_dock.features() ==
                QtWidgets.QDockWidget.DockWidgetClosable
                | QtWidgets.QDockWidget.DockWidgetMovable
                | QtWidgets.QDockWidget.DockWidgetFloatable)
        # Is the logger widget properly set?
        assert isinstance(logger_dock.widget(), logger.Logger)

    def test_hsplitter(self, launcher):
        hsplitter = launcher.gui.centralWidget().findChild(QtWidgets.QSplitter,
                                                           'hsplitter')
        assert hsplitter
        assert hsplitter.count() == 2
        assert hsplitter.indexOf(launcher.gui.dbs_tree_view) == 0
        assert hsplitter.indexOf(launcher.gui.workspace) == 1

    def test_actions(self, launcher):
        gui_actions = launcher.gui.gui_actions.keys()
        expected_actions = \
            ['fileNew', 'fileOpen', 'fileOpenRO', 'fileClose', 'fileCloseAll',
             'fileSaveAs', 'fileExit', 'nodeOpen', 'nodeClose',
             'nodeProperties', 'nodeNew', 'nodeRename', 'nodeCut', 'nodeCopy',
             'nodePaste', 'nodeDelete', 'queryNew', 'queryDeleteAll',
             'settingsPreferences', 'windowCascade', 'windowTile',
             'windowRestoreAll', 'windowMinimizeAll', 'windowClose',
             'windowCloseAll', 'windowSeparator', 'mdiTabbed',
             'helpUsersGuide', 'helpAbout', 'helpAboutQt', 'helpVersions',
             'calculate']
        assert sorted(gui_actions) == sorted(expected_actions)

    def test_toolbars(self, launcher):
        assert launcher.gui.findChild(QtWidgets.QToolBar, 'File toolbar')
        assert launcher.gui.findChild(QtWidgets.QToolBar, 'Node toolbar')
        assert launcher.gui.findChild(QtWidgets.QToolBar, 'Query toolbar')
        assert launcher.gui.findChild(QtWidgets.QToolBar, 'Help toolbar')

    def test_fileToolBar(self, launcher):
        file_tb = launcher.gui.file_toolbar
        tb_actions = [a.objectName() for a in file_tb.actions()]
        expected_actions = ['fileNew', 'fileOpen', 'fileClose', 'fileSaveAs']
        assert sorted(tb_actions) == sorted(expected_actions)

    def test_nodeToolBar(self, launcher):
        node_tb = launcher.gui.node_toolbar
        tb_actions = [a.objectName() for a in node_tb.actions()]
        expected_actions = ['nodeNew', 'nodeCut', 'nodeCopy', 'nodePaste',
                            'nodeDelete']
        assert sorted(tb_actions) == sorted(expected_actions)

    def test_queryToolBar(self, launcher):
        query_tb = launcher.gui.query_toolbar
        tb_actions = [a.objectName() for a in query_tb.actions()]
        expected_actions = ['queryNew', 'queryDeleteAll']
        assert sorted(tb_actions) == sorted(expected_actions)

    def test_helpToolBar(self, launcher):
        help_tb = launcher.gui.help_toolbar
        tb_actions = [a.objectName() for a in help_tb.actions()]
        expected_actions = ['helpUsersGuide', 'whatis']
        assert sorted(tb_actions) == sorted(expected_actions)

    def test_statusBarWidget(self, launcher):
        sbw = launcher.gui.statusBar().findChild(QtWidgets.QLabel,
                                                 'status bar widget')
        assert sbw
        sbw_sp = sbw.sizePolicy()
        hsp, vsp = sbw_sp.horizontalPolicy(), sbw_sp.verticalPolicy()
        assert hsp == QtWidgets.QSizePolicy.MinimumExpanding
        assert vsp == QtWidgets.QSizePolicy.Minimum

    @pytest.fixture()
    def menuBar(self, launcher):
        return launcher.gui.menuBar()

    def test_menus(self, menuBar):
        assert len(menuBar.actions()) == 6

    def test_fileMenu(self, menuBar):
        assert menuBar.findChild(QtWidgets.QMenu, 'file_menu')

    def test_nodeMenu(self, menuBar):
        assert menuBar.findChild(QtWidgets.QMenu, 'node_menu')

    def test_datasetMenu(self, menuBar):
        assert menuBar.findChild(QtWidgets.QMenu, 'dataset_menu')

    def test_settingsMenu(self, menuBar):
        assert menuBar.findChild(QtWidgets.QMenu, 'settings_menu')

    def test_windowMenu(self, menuBar):
        assert menuBar.findChild(QtWidgets.QMenu, 'window_menu')

    def test_helpMenu(self, menuBar):
        assert menuBar.findChild(QtWidgets.QMenu, 'help_menu')

