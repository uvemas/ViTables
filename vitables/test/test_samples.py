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
        'examples/arrays/array_samples.h5': [
            'array_b', 'array_f', 'array_f3D', 'array_int16', 'array_int8',
            'group1/array_B', 'group2/array_h', 'group3/array_l',
            'group4/array_f', 'group5/array_d', 'scalar_array',
        ],
        'examples/arrays/carray_sample.h5': [
            'carray',
        ],
        'examples/arrays/earray_samples.h5': [
            'array_b', 'array_c', 'array_char', 'array_e',
        ],
        'examples/arrays/vlarray_samples.h5': [
            'vlarray1', 'vlarray11', 'vlarray2', 'vlarray3', 'vlarray5',
            'vlarray6', 'vlarray8', 'vlarray10', 'vlarray9',
            # 'vlarray7',
        ],
        'examples/misc/external_file.h5': [
            'a1',
        ],
        # modified on open !!!
        # 'examples/misc/fnode.h5': [
        #     'fnode_test',
        # ],
        # modified on open !!!
        # 'examples/misc/genericHDF5.h5': [
        #     'A note', 'arrays/2D float array', 'arrays/2D int array',
        #     'arrays/3D int array',
        #     'arrays/Vdata table: PerBlockMetadataCommon',
        #     'arrays/external',
        #     # 'images/iceberg_palette',
        #     # 'images/Iceberg',
        #     # 'images/landcover.umd.199906.jpg',
        #     # 'images/pixel interlace',
        #     # 'images/plane interlace',
        # ],
        'examples/misc/links_examples.h5': [
            'arrays/a1', 'links/ht1', 'tables/t1',
        ],
        # modified on open !!!
        # 'examples/misc/nonalphanum.h5': [
        #     'array_1', 'array_f', 'array_f_Numeric', 'array_s',
        # ],
        'examples/misc/objecttree.h5': [
            'array1', 'group1/array2', 'group1/table1', 'group2/table2',
        ],
        'examples/misc/szip_compressor.h5': [
            # 'datasetF32',
        ],
        'examples/tables/nested_samples.h5': [
            'table',
        ],
        'examples/tables/table_samples.h5': [
            'columns/TDC', 'columns/name', 'columns/pressure',
            'detector/recarray', 'detector/recarray2', 'detector/table',
            'newgroup/table', 'table1',
        ],
        'examples/timeseries/carray_ts.h5': [
            'test_carray_1', 'test_carray_2',
        ],
        'examples/timeseries/pandas_test1.hdf5': [
            # 'one_column_ts/_i_table/index/abounds',
            # 'one_column_ts/_i_table/index/bounds',
            # 'one_column_ts/_i_table/index/indices',
            # 'one_column_ts/_i_table/index/indicesLR',
            # 'one_column_ts/_i_table/index/mbounds',
            # 'one_column_ts/_i_table/index/mranges',
            # 'one_column_ts/_i_table/index/ranges',
            # 'one_column_ts/_i_table/index/sorted',
            # 'one_column_ts/_i_table/index/sortedLR',
            # 'one_column_ts/_i_table/index/zbounds',
            # 'one_column_ts/table',
        ],
        'examples/timeseries/pandas_test2.hdf5': [
            # 'intc/_i_table/index/abounds', 'intc/_i_table/index/bounds',
            # 'intc/_i_table/index/indices', 'intc/_i_table/index/indicesLR',
            # 'intc/_i_table/index/mbounds', 'intc/_i_table/index/mranges',
            # 'intc/_i_table/index/ranges', 'intc/_i_table/index/sorted',
            # 'intc/_i_table/index/sortedLR', 'intc/_i_table/index/zbounds',
            # 'intc/table',
        ],
        'examples/timeseries/pandas_test3.hdf5': [
            # 'df/axis0', 'df/axis1', 'df/block0_items', 'df/block0_values',
            # 'df_table/_i_table/index/abounds',
            # 'df_table/_i_table/index/bounds',
            # 'df_table/_i_table/index/indices',
            # 'df_table/_i_table/index/indicesLR',
            # 'df_table/_i_table/index/mbounds',
            # 'df_table/_i_table/index/mranges',
            # 'df_table/_i_table/index/ranges',
            # 'df_table/_i_table/index/sorted',
            # 'df_table/_i_table/index/sortedLR',
            # 'df_table/_i_table/index/zbounds',
            'df_table/table',
        ],
        # modified on open !!!
        # 'examples/timeseries/scikits_test1.hdf5': [
        #     'examples/Example_1',
        # ],
        # modified on open !!!
        # 'examples/timeseries/scikits_test2.hdf5': [
        #     'examples/Example_2',
        # ],
        # modified on open !!!
        # 'examples/timeseries/scikits_test3.hdf5': [
        #     'examples/Example_3',
        # ],
        'examples/timeseries/table_ts.h5': [
            'Particles/TParticle',
        ],
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
        try:
            leaf_model = get_leaf_model_with_assert(self, filepath, nodepath)
            for row in range(leaf_model.rowCount()):
                for column in range(leaf_model.columnCount()):
                    cell_index = leaf_model.index(row, column,
                                                  qtcore.QModelIndex())
                    cell_data = leaf_model.data(cell_index)
        finally:
            self.vtapp.fileClose()
