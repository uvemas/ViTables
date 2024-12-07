"""Test class for utils.py"""

import pytest
from qtpy import QtGui, QtWidgets

import vitables.utils as utils


@pytest.mark.usefixtures('launcher')
class TestUtils(object):
    def test_getVTApp(self):
        vtapp = utils.getVTApp()
        assert vtapp.objectName() == 'VTApp'

    def test_getGui(self):
        gui = utils.getGui()
        assert gui.objectName() == 'VTGUI'

    def test_getModel(self):
        model = utils.getModel()
        assert model.objectName() == 'dbs_tree_model'

    def test_getView(self):
        view = utils.getView()
        assert view.objectName() == 'dbs_tree_view'

    def test_getSelectedIndexes(self):
        pass

    def test_getSelectedNodes(self):
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

    def test_insertInMenu(self, actions):
        uid = 'helpUsersGuide'

        # Insert a new action atop of the menu
        utils.insertInMenu(actions['help_menu'], actions['new_action'], uid)
        hm_actions = actions['help_menu'].actions()
        assert (hm_actions[0].objectName() ==
                actions['new_action'].objectName())
        actions['help_menu'].removeAction(hm_actions[0])

        # Insert a new menu atop of the menu
        utils.insertInMenu(actions['help_menu'], actions['new_menu'], uid)
        hm_actions = actions['help_menu'].actions()
        assert (hm_actions[0].menu().objectName() ==
                actions['new_menu'].objectName())
        actions['help_menu'].removeAction(hm_actions[0])

    def test_addToMenu(self, actions):
        # Append a new action
        utils.addToMenu(actions['help_menu'], actions['new_action'])
        hm_actions = actions['help_menu'].actions()
        assert (hm_actions[-1].objectName() ==
                actions['new_action'].objectName())
        actions['help_menu'].removeAction(hm_actions[-1])

        # Append a new menu
        utils.addToMenu(actions['help_menu'], actions['new_menu'])
        hm_actions = actions['help_menu'].actions()
        assert (hm_actions[-1].menu().objectName() ==
                actions['new_menu'].objectName())
        actions['help_menu'].removeAction(hm_actions[-1])

    def test_addActions(self, actions):
        utils.addActions(actions['help_menu'], [None], {})
        hm_actions = actions['help_menu'].actions()
        assert hm_actions[-1].isSeparator()
        actions['help_menu'].removeAction(hm_actions[-1])

        utils.addActions(actions['help_menu'], [actions['new_menu']], {})
        hm_actions = actions['help_menu'].actions()
        assert hm_actions[-1].menu() is not None
        actions['help_menu'].removeAction(hm_actions[-1])

        utils.addActions(actions['help_menu'], ['new_action'],
                         {'new_action': actions['new_action']})
        hm_actions = actions['help_menu'].actions()
        assert hm_actions[-1].objectName() == 'testaction'
        actions['help_menu'].removeAction(hm_actions[-1])

    def test_checkFileExtension(self):
        assert utils.checkFileExtension('test') == 'test.h5'
        assert utils.checkFileExtension('test.ext') == 'test.ext'

    def test_createIcons(self):
        large_icons = frozenset(['document-close'])
        small_icons = frozenset(['document-close'])
        icons_dict = {}
        utils.createIcons(large_icons, small_icons, icons_dict)
        assert sorted(icons_dict.keys()) == ['', 'document-close',
                                             'vitables_wm']
        assert isinstance(icons_dict['document-close'], QtGui.QIcon)

    def test_forwardPath(self):
        filepath = 'C:\\Users\\my_name\\Desktop\\'
        assert utils.forwardPath(filepath) == 'C:/Users/my_name/Desktop/'
