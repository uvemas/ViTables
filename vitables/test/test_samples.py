import sys
import os.path
import unittest

import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

import PyQt4.QtGui as qtgui
import PyQt4.QtCore as qtcore
import PyQt4.QtTest as qtest

import vitables.start as vtstart

from vitables.vtapp import VTApp
from vitables.preferences import vtconfig

TABLES_PATH = os.path.join('examples', 'tables')


def get_index(model, node_name, start_index=None):
    """Return index of the node with the given name or None."""
    start_index = start_index if start_index else qtcore.QModelIndex()
    for c in range(model.columnCount(start_index)):
        for r in range(model.rowCount(start_index)):
            index = model.index(r, c, start_index)
            if index.data(qtcore.Qt.DisplayRole) == node_name:
                return index
            child_search_result = get_index(model, node_name, index)
            if child_search_result:
                return child_search_result
    return None


def assert_path(test, model, view, path):
    """Activate and check that node at given path exist.

    If the last node is a leaf then subwindow will be created.
    """
    if not path:
        return
    index = get_index(model, path[0])
    test.assertFalse(index is None)
    view.activateNode(index)
    assert_path(test, model, view, path[1:])


def get_leaf_model_with_assert(test, filepath, leaf_path):
    """Open view for given leaf and return its model.

    filepath is a valid system path, node_path is a slash separated leaf
    path inside file without preceding slash.
    """
    leaf_path = leaf_path.split('/')
    _, filename = os.path.split(filepath)
    test.vtapp.fileOpen(filepath)
    assert_path(test, test.model, test.view, [filename] + leaf_path)
    return test.vtgui.workspace.subWindowList()[0].leaf_model


class TestTableOpening(unittest.TestCase):
    def setUp(self):
        self.app = qtgui.QApplication(sys.argv)
        self.vtapp = VTApp(keep_splash=False)
        self.vtgui = self.vtapp.gui
        self.model = self.vtgui.dbs_tree_model
        self.view = self.vtgui.dbs_tree_view

    def test_nested(self):
        filepath = 'examples/tables/nested_samples.h5'
        leaf_model = get_leaf_model_with_assert(self, filepath, 'table')
        cell_data = leaf_model.data(leaf_model.index(0, 3))
        # print(cell_data)
        # self.vtgui.show()
        # self.app.exec_()
