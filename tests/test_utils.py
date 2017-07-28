"""Test class for utils.py"""

import sys

import pytest

# from qtpy import QtTest
from qtpy import QtWidgets

import vitables.vtapp
import vitables.utils as utils


class TestUtils(object):
    @pytest.fixture(scope='module')
    def launcher(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.vtapp_object = vitables.vtapp.VTApp(keep_splash=False)

    def test_getvtapp(self, launcher):
        vtapp = utils.getVTApp()
        assert vtapp.objectName() == 'VTApp'

    def test_getgui(self, launcher):
        gui = utils.getGui()
        assert gui.objectName() == 'VTGUI'

    def test_getmodel(self, launcher):
        model = utils.getModel()
        assert model.objectName() == 'dbs_tree_model'

    def test_getview(self, launcher):
        view = utils.getView()
        assert view.objectName() == 'dbs_tree_view'

    def test_getselectedindexes(self, launcher):
        pass

    def test_getselectednodes(self, launcher):
        pass

    def test_longaction(self, launcher):
        pass

    def test_insertinmenu(self, launcher):
        # The menu to be enlarged
        menubar = utils.getGui().menuBar()
        help_menu = menubar.findChild(QtWidgets.QMenu, 'help_menu')
        uid = 'helpUsersGuide'

        # The objects to be inserted

        # Insert a new action atop of the menu
        new_action = QtWidgets.QAction('TestAction')
        new_action.setObjectName('testaction')
        utils.insertInMenu(help_menu, new_action, uid)
        actions = help_menu.actions()
        assert actions[0].objectName() == new_action.objectName()
        help_menu.removeAction(new_action)

        # Insert a new menu atop of the menu
        new_menu = QtWidgets.QMenu('TestMenu')
        new_menu.setObjectName('testmenu')
        utils.insertInMenu(help_menu, new_menu, uid)
        actions = help_menu.actions()
        assert actions[0].menu().objectName() == new_menu.objectName()
        help_menu.removeAction(new_action)


