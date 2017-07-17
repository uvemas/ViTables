#       Copyright (C) 2008-2017 Vicent Mas. All rights reserved
#
#       This program is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#       Author:  Vicent Mas - vmas@vitables.org

#
# Initial draft author: Jorge Ibanez jorge.ibannez@uam.es
#

"""Module that provides import `CSV` files into `PyTables` arrays and tables.

The pipeline for importing a `CSV` file is::

    CSV file --> numpy array --> tables.Leaf

The ``numpy`` array is created via `numpy.genfromtxt`. The `tables.Leaf`
instance is created using the appropriate constructors.

Beware that importing big files is a slow process because the whole file
has to be read from disk, transformed and write back to disk again so
there is a lot of disk IO.

Other aspects to take into account:

  - creation of `tables.Array` datasets requires the ``numpy`` array containing
    the whole `CSV` file to be loaded in memory. If the file is large enough
    you can run out of memory.

  - creation of `tables.CArray` datasets requires an additional parsing of the
    whole `CSV` file in order to find out its number of rows (it is a required
    argument of the `tables.CArray` constructor).

  - there is a penalty performance when string dtypes are involved. The reason
    is that string fields use to have variable length so, before the ``numpy``
    array is created, we need to find out the minimum itemsize required for
    storing those string fields with no lose of data. This step requires an
    additional parsing of the whole `CSV` file.

  - `CSV` files containing N-dimensional fields are always imported with `str`
    dtype. This is a limitation of `numpy.genfromtxt`.
"""

import logging
import os
import traceback

import numpy
import tables
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.csv.csvutils as csvutils
import vitables.utils

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate
TYPE_ERROR = translate(
    'ImportCSV', 'Please, make sure that you are importing a '
    'homogeneous dataset.', 'CSV file not imported error')

log = logging.getLogger(__name__)


class ImportCSV(QtCore.QObject):
    """Provides CSV import capabilities for tables and arrays.

    Some minor flaws: multidimensional fields are not well supported.
    They are imported as strings.
    """

    def __init__(self):
        """The class constructor.
        """

        super(ImportCSV, self).__init__()

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()
        if self.vtapp is None:
            return

        self.vtgui = vitables.utils.getGui()
        self.dbt_model = self.vtgui.dbs_tree_model
        self.dbt_view = self.vtgui.dbs_tree_view

        # Add an entry under the File menu
        self.icons_dictionary = vitables.utils.getIcons()
        self.addEntry()

    def addEntry(self):
        """Add the `Import CSV...` entry to the `File` menu.
        """

        self.import_csv_submenu = QtWidgets.QMenu(
            translate('ImportCSV', 'I&mport from CSV...',
                      'File -> Import CSV'))
        self.import_csv_submenu.setSeparatorsCollapsible(False)
        self.import_csv_submenu.setIcon(
            self.icons_dictionary['document-import'])
        self.import_csv_submenu.setObjectName('import_csv_submenu')

        # Create the actions
        actions = {}
        actions['import_csv_table'] = QtWidgets.QAction(
            translate('ImportCSV', "Import &Table...",
                      "Import table from CSV file"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.csv2Table,
            statusTip=translate(
                'ImportCSV',
                "Import Table from plain CSV file",
                "Status bar text for File -> Import CSV... -> Import Table"))
        actions['import_csv_table'].setObjectName('import_csv_table')

        actions['import_csv_array'] = QtWidgets.QAction(
            translate('ImportCSV', "Import &Array...",
                      "Import array from CSV file"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.csv2Array,
            statusTip=translate(
                'ImportCSV',
                "Import Array from plain CSV file",
                "Status bar text for File -> Import CSV... -> Import Array"))
        actions['import_csv_array'].setObjectName('import_csv_array')

        actions['import_csv_carray'] = QtWidgets.QAction(
            translate('ImportCSV', "Import &CArray...",
                      "Import carray from CSV file"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.csv2CArray,
            statusTip=translate(
                'ImportCSV',
                "Import CArray from plain CSV file",
                "Status bar text for File -> Import CSV... -> Import CArray"))
        actions['import_csv_carray'].setObjectName('import_csv_carray')

        actions['import_csv_earray'] = QtWidgets.QAction(
            translate('ImportCSV', "Import &EArray...",
                      "Import earray from CSV file"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.csv2EArray,
            statusTip=translate(
                'ImportCSV',
                "Import EArray from plain CSV file",
                "Status bar text for File -> Import CSV... -> Import EArray"))
        actions['import_csv_earray'].setObjectName('import_csv_earray')

        actions['import_csv_separator'] = QtWidgets.QAction(self)
        actions['import_csv_separator'].setSeparator(True)
        actions['import_csv_separator'].setObjectName('import_csv_separator')

        # Add actions to the Import submenu
        keys = ('import_csv_table', 'import_csv_array', 'import_csv_carray',
                'import_csv_earray')
        vitables.utils.addActions(self.import_csv_submenu, keys, actions)

        # Add submenu to file menu before the Close File action
        vitables.utils.insertInMenu(
            self.vtgui.file_menu, self.import_csv_submenu, 'fileClose')
        sep = actions['import_csv_separator']
        vitables.utils.insertInMenu(self.vtgui.file_menu, sep, 'fileClose')

        # Add submenu to file context menu before the Close File action
        vitables.utils.insertInMenu(self.vtgui.view_cm,
                                    self.import_csv_submenu, 'fileClose')
        vitables.utils.insertInMenu(self.vtgui.view_cm, sep, 'fileClose')

    def createDestFile(self, filepath):
        """Create the `PyTables` file where the `CSV` file will be imported.

        :Parameter filepath: the `PyTables` file filepath
        """

        dbdoc = None
        try:
            dirname, filename = os.path.split(filepath)
            root = os.path.splitext(filename)[0]
            dest_filepath = vitables.utils.forwardPath(os.path.join(dirname,
                                                                    '{0}.h5'.format(root)))
            if csvutils.isValidFilepath(dest_filepath):
                dbdoc = self.dbt_model.createDBDoc(dest_filepath)
        except:
            log.error(
                translate('ImportCSV', 'Import failed because destination '
                          'file cannot be created.',
                          'A file creation error'))
            vitables.utils.formatExceptionInfo()

        return dbdoc

    def csvFilepath(self, leaf_kind):
        """Get the filepath of the source `CSV` file.

        :Parameter leaf_kind: the kind of container where data will be stored
        """

        # Call the file selector (and, if needed, customise it)
        filepath, working_dir = vitables.utils.getFilepath(
            self.vtgui, translate(
                'ImportCSV', 'Importing CSV file into {0}',
                'Caption of the Import from CSV dialog').format(leaf_kind),
            dfilter=translate('ImportCSV', """CSV Files (*.csv);;"""
                              """All Files (*)""",
                              'Filter for the Import from CSV dialog'),
            settings={'accept_mode': QtWidgets.QFileDialog.AcceptOpen,
                      'file_mode': QtWidgets.QFileDialog.ExistingFile,
                      'history': self.vtapp.file_selector_history,
                      'label': translate('ImportCSV', 'Import',
                                         'Accept button text for QFileDialog')}
        )

        if not filepath:
            # The user has canceled the dialog
            return

        # Update the history of the file selector widget
        self.vtapp.updateFSHistory(working_dir)

        return filepath

    def updateTree(self, filepath):
        """Update the databases tree once the `CSV` file has been imported.

        When the destination h5 file is created and added to the databases tree
        it has no nodes. Once the `CSV` file has been imported into a
        `PyTables` container we update the representation of the h5 file in the
        tree so that users can see that the file has a leaf. Eventually, the
        root node of the imported file is selected so that users can locate it
        immediately.

        :Parameter filepath: the filepath of the destination h5 file
        """

        for row, child in enumerate(self.dbt_model.root.children):
            if child.filepath == filepath:
                index = self.dbt_model.index(row, 0, QtCore.QModelIndex())
                self.dbt_model.lazyAddChildren(index)
                self.dbt_view.setCurrentIndex(index)

    def csv2Table(self):
        """Import a plain `CSV` file into a `tables.Array` object.
        """

        kind = 'Table'
        filepath = self.csvFilepath(kind)
        if filepath is None:
            return

        # Import the CSV content
        try:
            QtWidgets.qApp.processEvents()
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            input_handler = open(filepath, 'r+')
            try:
                (nrows, descr, has_header) = csvutils.tableInfo(input_handler)
            except Exception as inst:
                print(traceback.format_exc())

            # Create the dataset
            dbdoc = self.createDestFile(filepath)
            if dbdoc is None:
                return
            io_filters = tables.Filters(complevel=9, complib='lzo')
            dataset_name = "imported_{0}".format(kind)
            atitle = \
                'Source CSV file {0}'.format(os.path.basename(filepath))
            dataset = dbdoc.h5file.create_table(
                '/', dataset_name, descr, title=atitle, filters=io_filters,
                expectedrows=nrows)
            # Fill the dataset in a memory efficient way
            input_handler.seek(0)
            if has_header:
                # Skip the header line
                input_handler.readline()
            chunk_size = 10000
            buf_size = chunk_size * dataset.rowsize
            read_fh = input_handler.readlines
            buf = read_fh(buf_size)
            while buf:
                idata = csvutils.getArray(buf)
                # Append data to the dataset
                dataset.append(idata)
                dataset.flush()
                del idata
                buf = read_fh(buf_size)
            dbdoc.h5file.flush()
            self.updateTree(dbdoc.filepath)
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtWidgets.qApp.restoreOverrideCursor()
            input_handler.close()

    def csv2EArray(self):
        """Import a plain `CSV` file into a `tables.EArray` object.

        This is a slot method. See :meth:`addEntry` method for details.
        """

        kind = 'EArray'
        filepath = self.csvFilepath(kind)
        if filepath is None:
            return

        # Import the CSV content
        try:
            QtWidgets.qApp.processEvents()
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            chunk_size = 10000
            input_handler = open(filepath, 'r+')
            (nrows, atom, array_shape) = csvutils.earrayInfo(input_handler)

            # Create the dataset
            dbdoc = self.createDestFile(filepath)
            if dbdoc is None:
                return
            io_filters = tables.Filters(complevel=9, complib='lzo')
            dataset_name = "imported_{0}".format(kind)
            atitle = 'Source CSV file {0}'.format(os.path.basename(filepath))
            dataset = dbdoc.h5file.create_earray(
                '/', dataset_name, atom, array_shape, title=atitle,
                filters=io_filters, expectedrows=nrows)

            # Fill the dataset in a memory effcient way
            input_handler.seek(0)
            chunk_size = 10000
            buf_size = chunk_size * dataset.rowsize
            read_fh = input_handler.readlines
            buf = read_fh(buf_size)
            while buf:
                idata = csvutils.getArray(buf)
                # Append data to the dataset
                dataset.append(idata)
                dataset.flush()
                del idata
                buf = read_fh(buf_size)
            dbdoc.h5file.flush()
            self.updateTree(dbdoc.filepath)
        except ValueError:
            log.error(TYPE_ERROR)
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtWidgets.qApp.restoreOverrideCursor()
            input_handler.close()

    def csv2CArray(self):
        """Import a plain `CSV` file into a `tables.CArray` object.

        This is a slot method. See :meth:`addEntry` method for details.
        """

        kind = 'CArray'
        filepath = self.csvFilepath(kind)
        if filepath is None:
            return

        # Import the CSV content
        try:
            QtWidgets.qApp.processEvents()
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            chunk_size = 10000
            input_handler = open(filepath, 'r+')
            (atom, array_shape) = csvutils.carrayInfo(input_handler)

            # Create the dataset
            dbdoc = self.createDestFile(filepath)
            if dbdoc is None:
                return
            io_filters = tables.Filters(complevel=9, complib='lzo')
            dataset_name = "imported_{0}".format(kind)
            atitle = 'Source CSV file {0}'.format(os.path.basename(filepath))
            dataset = dbdoc.h5file.create_carray(
                '/', dataset_name, atom, array_shape, title=atitle,
                filters=io_filters)

            # Fill the dataset in a memory effcient way
            input_handler.seek(0)
            chunk_size = 10000
            buf_size = chunk_size * dataset.rowsize
            read_fh = input_handler.readlines
            buf = read_fh(buf_size)
            start = 0
            while buf:
                idata = csvutils.getArray(buf)
                stop = start + idata.shape[0]
                # Append data to the dataset
                dataset[start:stop] = idata
                dataset.flush()
                del idata
                start = stop
                buf = read_fh(buf_size)
            dbdoc.h5file.flush()
            self.updateTree(dbdoc.filepath)
        except ValueError:
            log.error(TYPE_ERROR)
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtWidgets.qApp.restoreOverrideCursor()
            input_handler.close()

    def csv2Array(self):
        """Import a plain `CSV` file into a `tables.Array` object.

        This is a slot method. See :meth:`addEntry` method for details.
        """

        kind = 'Array'
        filepath = self.csvFilepath(kind)
        if filepath is None:
            return

        # Import the CSV content
        try:
            QtWidgets.qApp.processEvents()
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            # The dtypes are determined by the contents of each column
            # Multidimensional columns will have string datatype
            data = numpy.genfromtxt(filepath, delimiter=',', dtype=None)
        except TypeError:
            data = None
            dbdoc = None
            log.error(TYPE_ERROR)
        else:
            try:
                # Create the array
                dbdoc = self.createDestFile(filepath)
                if dbdoc is None:
                    return
                array_name = "imported_{0}".format(kind)
                title = 'Imported from CSV file {0}'.\
                    format(os.path.basename(filepath))
                dbdoc.h5file.create_array('/', array_name, data, title=title)
                dbdoc.h5file.flush()
                self.updateTree(dbdoc.filepath)
            except TypeError:
                log.error(TYPE_ERROR)
            except tables.NodeError:
                vitables.utils.formatExceptionInfo()
        finally:
            del data
            QtWidgets.qApp.restoreOverrideCursor()
