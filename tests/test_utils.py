"""Test class for utils.py"""

import pytest

# from qtpy import QtTest
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.utils as utils


@pytest.mark.usefixtures('launcher')
class TestUtils(object):
    def test_getvtapp(self):
        vtapp = utils.getVTApp()
        assert vtapp.objectName() == 'VTApp'

    def test_getgui(self):
        gui = utils.getGui()
        assert gui.objectName() == 'VTGUI'

    def test_getmodel(self):
        model = utils.getModel()
        assert model.objectName() == 'dbs_tree_model'

    def test_getview(self):
        view = utils.getView()
        assert view.objectName() == 'dbs_tree_view'

    def test_getselectedindexes(self):
        pass

    def test_getselectednodes(self):
        pass

    def test_longaction(self):
        pass

    @pytest.fixture()
    def actions(self):
        # Menu to be enlarged
        menubar = utils.getGui().menuBar()
        help_menu = menubar.findChild(QtWidgets.QMenu, 'help_menu')

        # Actions to insert/append
        new_action = QtWidgets.QAction('TestAction')
        new_action.setObjectName('testaction')
        new_menu = QtWidgets.QMenu('TestMenu')
        new_menu.setObjectName('testmenu')

        return {
            'help_menu': help_menu,
            'new_action': new_action,
            'new_menu': new_menu,
        }

    def test_insertinmenu(self, actions):
        uid = 'helpUsersGuide'

        # Insert a new action atop of the menu
        utils.insertInMenu(actions['help_menu'], actions['new_action'], uid)
        hm_actions = actions['help_menu'].actions()
        assert hm_actions[0].objectName() == actions['new_action'].objectName()
        actions['help_menu'].removeAction(hm_actions[0])

        # Insert a new menu atop of the menu
        utils.insertInMenu(actions['help_menu'], actions['new_menu'], uid)
        hm_actions = actions['help_menu'].actions()
        assert hm_actions[0].menu().objectName() == actions['new_menu'].objectName()
        actions['help_menu'].removeAction(hm_actions[0])

    def test_addtomenu(self, actions):
        # Append a new action
        utils.addToMenu(actions['help_menu'], actions['new_action'])
        hm_actions = actions['help_menu'].actions()
        assert hm_actions[-1].objectName() == actions['new_action'].objectName()
        actions['help_menu'].removeAction(hm_actions[-1])

        # Append a new menu
        utils.addToMenu(actions['help_menu'], actions['new_menu'])
        hm_actions = actions['help_menu'].actions()
        assert hm_actions[-1].menu().objectName() == actions['new_menu'].objectName()
        actions['help_menu'].removeAction(hm_actions[-1])

    def test_getfileselector(self):
        pass

    def test_getfilepath(self):
        pass

    def test_getfileextension(self):
        assert utils.checkFileExtension('test') == 'test.h5'
        assert utils.checkFileExtension(('test.ext')) == 'test.ext'

    def test_createicons(self):
        large_icons = frozenset(['document-close'])
        small_icons = frozenset(['document-close'])
        icons_dict = {}
        utils.createIcons(large_icons, small_icons, icons_dict)
        assert sorted(icons_dict.keys()) == ['', 'document-close', 'vitables_wm']
        assert isinstance(icons_dict['document-close'], QtGui.QIcon)