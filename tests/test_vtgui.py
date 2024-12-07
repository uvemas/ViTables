"""Test class for vtgui.py"""

import pytest
from qtpy import QtCore, QtWidgets

from vitables import logger


@pytest.mark.usefixtures('launcher')
class TestVTGui:
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

    def test_fileToolBar(self, launcher):
        file_tb = launcher.gui.findChild(QtWidgets.QToolBar, 'File toolbar')
        assert file_tb

        tb_actions = [a.objectName() for a in file_tb.actions()]
        expected_actions = ['fileNew', 'fileOpen', 'fileClose', 'fileSaveAs']
        assert sorted(tb_actions) == sorted(expected_actions)

    def test_nodeToolBar(self, launcher):
        node_tb = launcher.gui.findChild(QtWidgets.QToolBar, 'Node toolbar')
        assert node_tb

        tb_actions = [a.objectName() for a in node_tb.actions()]
        expected_actions = ['nodeNew', 'nodeCut', 'nodeCopy', 'nodePaste',
                            'nodeDelete']
        assert sorted(tb_actions) == sorted(expected_actions)

    def test_queryToolBar(self, launcher):
        query_tb = launcher.gui.findChild(QtWidgets.QToolBar, 'Query toolbar')
        assert query_tb

        tb_actions = [a.objectName() for a in query_tb.actions()]
        expected_actions = ['queryNew', 'queryDeleteAll']
        assert sorted(tb_actions) == sorted(expected_actions)

    def test_helpToolBar(self, launcher):
        help_tb = launcher.gui.findChild(QtWidgets.QToolBar, 'Help toolbar')
        assert help_tb

        tb_actions = [a.objectName() for a in help_tb.actions()]
        expected_actions = ['helpUsersGuide', 'whatis_help_toolbar']
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
        menu = menuBar.findChild(QtWidgets.QMenu, 'file_menu')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['fileNew', 'fileOpen', 'fileOpenRO', 'fileClose',
                            'fileCloseAll', 'fileSaveAs', 'fileExit']
        assert sorted(actions) == sorted(expected_actions)

        menus = [a.menu().objectName() for a in menu_actions if a.menu()]
        assert sorted(menus) == ['import_csv_submenu', 'open_recent_submenu']

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 4

    def test_nodeMenu(self, menuBar):
        menu = menuBar.findChild(QtWidgets.QMenu, 'node_menu')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['nodeOpen', 'nodeClose', 'nodeProperties',
                            'nodeNew', 'nodeRename', 'nodeCut', 'nodeCopy',
                            'nodePaste', 'nodeDelete']
        assert sorted(actions) == sorted(expected_actions)

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 1

    def test_datasetMenu(self, menuBar):
        menu = menuBar.findChild(QtWidgets.QMenu, 'dataset_menu')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['queryNew', 'calculate', 'export_csv']
        assert sorted(actions) == sorted(expected_actions)

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 1

    def test_settingsMenu(self, menuBar):
        menu = menuBar.findChild(QtWidgets.QMenu, 'settings_menu')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['settingsPreferences']
        assert sorted(actions) == sorted(expected_actions)

        menus = [a.menu().objectName() for a in menu_actions if a.menu()]
        assert sorted(menus) == ['settings_toolbars_submenu']

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 1

    def test_windowMenu(self, menuBar):
        menu = menuBar.findChild(QtWidgets.QMenu, 'window_menu')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['windowCascade', 'windowTile',
                           'windowRestoreAll', 'windowMinimizeAll',
                           'windowClose', 'windowCloseAll', 'mdiTabbed']
        assert sorted(actions) == sorted(expected_actions)

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 2

    def test_helpMenu(self, menuBar):
        menu = menuBar.findChild(QtWidgets.QMenu, 'help_menu')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['helpUsersGuide', 'helpAbout', 'helpAboutQt',
                        'helpVersions', 'whatis_help_menu']
        assert sorted(actions) == sorted(expected_actions)

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 2

    def test_viewCM(self, launcher):
        menu = launcher.gui.findChild(QtWidgets.QMenu, 'view_cm')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['fileNew', 'fileOpen', 'fileOpenRO', 'fileClose',
                            'fileCloseAll', 'fileSaveAs', 'fileExit']
        assert sorted(actions) == sorted(expected_actions)

        menus = [a.menu().objectName() for a in menu_actions if a.menu()]
        assert sorted(menus) == ['import_csv_submenu', 'open_recent_submenu']

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 4

    def test_rootNodeCM(self, launcher):
        menu = launcher.gui.findChild(QtWidgets.QMenu, 'root_node_cm')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['fileClose', 'fileSaveAs', 'nodeProperties',
                            'nodeNew', 'nodeCopy', 'nodePaste',
                            'queryDeleteAll']
        assert sorted(actions) == sorted(expected_actions)

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 3

    def test_groupNodeCM(self, launcher):
        menu = launcher.gui.findChild(QtWidgets.QMenu, 'group_node_cm')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['nodeProperties', 'nodeNew', 'nodeRename',
                            'nodeCut', 'nodeCopy', 'nodePaste', 'nodeDelete']
        assert sorted(actions) == sorted(expected_actions)

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 1

    def test_leafNodeCM(self, launcher):
        menu = launcher.gui.findChild(QtWidgets.QMenu, 'leaf_node_cm')
        menu_actions = menu.actions()
        assert menu

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['nodeOpen', 'nodeClose',  'nodeProperties',
                            'nodeRename', 'nodeCut', 'nodeCopy', 'nodePaste',
                            'nodeDelete', 'queryNew', 'export_csv']
        assert sorted(actions) == sorted(expected_actions)

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 4

    def test_mdiCM(self, launcher):
        menu = launcher.gui.findChild(QtWidgets.QMenu, 'mdi_cm')
        menu_actions = menu.actions()
        assert menu

        menus = [a.menu().objectName() for a in menu_actions if a.menu()]
        assert sorted(menus) == ['window_menu']
