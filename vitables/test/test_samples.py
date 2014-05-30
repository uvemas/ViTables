import sys
import os.path
import nose.tools as nt

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


def assert_path(test, path):
    """Activate and check that node at given path exist.

    If the last node is a leaf then subwindow will be created.
    """
    if not path:
        return
    index = get_index(test.model, path[0])
    nt.assert_false(index is None)
    test.view.activateNode(index)
    assert_path(test, path[1:])


def get_leaf_model_with_assert(test, filepath, leaf_path):
    """Open view for given leaf and return its model.

    filepath is a valid system path, node_path is a slash separated leaf
    path inside file without preceding slash.
    """
    leaf_path = leaf_path.split('/')
    _, filename = os.path.split(filepath)
    test.vtapp.fileOpen(filepath)
    assert_path(test, [filename] + leaf_path)
    return test.vtgui.workspace.subWindowList()[0].leaf_model


class TestTableOpening:
    """Open files and read all cell values."""

    TEST_NODES = {
        'examples/tables/nested_samples.h5': ['table'],
        'examples/tables/table_samples.h5': [
            'table1', 'columns/name', 'columns/pressure', 'columns/TDC',
            'newgroup/table', 'detector/recarray', 'detector/recarray2'],
        'examples/misc/external_file.h5': ['a1'],
        'examples/misc/fnode.h5': ['fnode_test'],
        'examples/misc/genericHDF5.h5': ['A note', 'images/Iceberg'],
        }

    @classmethod
    def setup_class(cls):
        """Create app and store shortcuts to the application objects."""
        cls.app = qtgui.QApplication(sys.argv)
        cls.vtapp = VTApp(keep_splash=False)
        cls.vtgui = cls.vtapp.gui
        cls.model = cls.vtgui.dbs_tree_model
        cls.view = cls.vtgui.dbs_tree_view

    def test_opening_files(self):
        """Generate tests for given data files."""
        for filepath, nodes in self.TEST_NODES.items():
            for node in nodes:
                yield self.check_node_open, filepath, node

    def check_node_open(self, filepath, nodepath):
        """Open file get access to a node and read all cells."""
        leaf_model = get_leaf_model_with_assert(self, filepath, nodepath)
        for row in range(leaf_model.rowCount()):
            for column in range(leaf_model.columnCount()):
                cell_index = leaf_model.index(row, column,
                                              qtcore.QModelIndex())
                cell_data = leaf_model.data(cell_index)
        self.vtapp.fileClose()
