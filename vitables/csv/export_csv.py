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

"""Plugin that provides export of `tables.Leaf` nodes into `CSV` files.

When exporting tables, a header with the field names can be inserted.

In general, tables/arrays with Ndimensional fields are not exported because they
are not written by np.savetxt() in a way compliant with the CSV format in which
each line of the file is a data record.

Neither numpy scalar arrays are exported.
"""


import logging
import os

import numpy
import tables
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.csv.csvutils as csvutils
import vitables.utils

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate

log = logging.getLogger(__name__)


class ExportToCSV(QtCore.QObject):
    """Provides `CSV` export capabilities for arrays.
    """

    def __init__(self):
        """The class constructor.
        """

        super(ExportToCSV, self).__init__()

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()
        if self.vtapp is None:
            return

        self.vtgui = vitables.utils.getGui()

        # Add an entry under the Dataset menu
        self.icons_dictionary = vitables.utils.getIcons()
        self.addEntry()

        # Connect signals to slots
        self.vtgui.dataset_menu.aboutToShow.connect(self.updateDatasetMenu)
        self.vtgui.leaf_node_cm.aboutToShow.connect(self.updateDatasetMenu)

    def addEntry(self):
        """Add the `Export to CSV..`. entry to `Dataset` menu.
        """

        self.export_csv_action = QtWidgets.QAction(
            translate('ExportToCSV', "E&xport to CSV...",
                      "Save dataset as CSV"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey, triggered=self.export,
            icon=vitables.utils.getIcons()['document-export'],
            statusTip=translate(
                'ExportToCSV',
                "Save the dataset as a plain text with CSV format",
                "Status bar text for the Dataset -> Export to CSV... action"))
        self.export_csv_action.setObjectName('export_csv')

        # Add the action to the Dataset menu
        vitables.utils.addToMenu(self.vtgui.dataset_menu, self.export_csv_action)

        # Add the action to the leaf context menu
        vitables.utils.addToLeafContextMenu(self.export_csv_action)

    def updateDatasetMenu(self):
        """Update the `export` QAction when the Dataset menu is pulled down.

        This method is a slot. See class ctor for details.
        """

        enabled = True
        current = self.vtgui.dbs_tree_view.currentIndex()
        if current:
            leaf = self.vtgui.dbs_tree_model.nodeFromIndex(current)
            if leaf.node_kind in ('group', 'root group'):
                enabled = False

        self.export_csv_action.setEnabled(enabled)

    def getExportInfo(self, is_table):
        """Get info about the file where dataset will be stored.

        The info is retrieved from the FileSelector dialog. The returned info
        is the filepath and whether or not a header must be added.

        :Parameter is_table: True if the exported dataset is a tables.Table
          instance
        """

        # Call the file selector (and, if needed, customise it)
        file_selector = vitables.utils.getFileSelector(
            self.vtgui,
            translate('ExportToCSV', 'Exporting dataset to CSV format',
                      'Caption of the Export to CSV dialog'),
            dfilter=translate('ExportToCSV', """CSV Files (*.csv);;"""
                              """All Files (*)""",
                              'Filter for the Export to CSV dialog'),
            settings={'accept_mode': QtWidgets.QFileDialog.AcceptSave,
                      'file_mode': QtWidgets.QFileDialog.AnyFile,
                      'history': self.vtapp.file_selector_history,
                      'label': translate('ExportToCSV', 'Export',
                                         'Accept button text for QFileDialog')}
        )

        # Customise the file selector dialog for exporting to CSV files
        if is_table:
            # We can get the layout of Qt dialogs but not of native dialogs
            file_selector.setOption(QtWidgets.QFileDialog.DontUseNativeDialog,
                                    True)
            fs_layout = file_selector.layout()
            header_label = QtWidgets.QLabel('Add header:', file_selector)
            header_cb = QtWidgets.QCheckBox(file_selector)
            header_cb.setChecked(True)
            fs_layout.addWidget(header_label, 4, 0)
            fs_layout.addWidget(header_cb, 4, 1)

        # Execute the dialog
        try:
            if file_selector.exec_():  # OK clicked
                filepath = file_selector.selectedFiles()[0]
                # Make sure filepath contains no backslashes
                filepath = QtCore.QDir.fromNativeSeparators(filepath)
                filepath = csvutils.checkFilenameExtension(filepath)
                # Update the working directory
                working_dir = file_selector.directory().canonicalPath()
            else:  # Cancel clicked
                filepath = working_dir = ''
        finally:
            add_header = False
            if is_table:
                add_header = header_cb.isChecked()
            del file_selector

        # Process the returned values
        if not filepath:
            # The user has canceled the dialog
            return

        # Update the history of the file selector widget
        self.vtapp.updateFSHistory(working_dir)

        # Check the returned path
        if os.path.exists(filepath):
            log.error(translate(
                'ExportToCSV',
                'Export failed because destination file already exists.',
                'A file creation error'))
            return

        if os.path.isdir(filepath):
            log.error(translate(
                'ExportToCSV',
                'Export failed because destination container is a directory.',
                'A file creation error'))
            return

        return filepath, add_header

    # def _try_exporting_dataframe(self, leaf):
    #     ## FIXME: Hack to export to csv.
    #     #
    #     from ...vttables import df_model
    #
    #     leaf_model = df_model.try_opening_as_dataframe(leaf)
    #     if not leaf_model:
    #         return
    #
    #     export_info = self.getExportInfo(is_table=True)
    #     if export_info is None:
    #         return
    #
    #     leaf_model.to_csv(*export_info)
    #     return True

    def export(self):
        """Export a given dataset to a `CSV` file.

        This method is a slot connected to the `export` QAction. See the
        :meth:`addEntry` method for details.
        """

        # The PyTables node tied to the current leaf of the databases tree
        current = self.vtgui.dbs_tree_view.currentIndex()
        leaf = self.vtgui.dbs_tree_model.nodeFromIndex(current).node

        # Empty datasets aren't saved as CSV files
        if leaf.nrows == 0:
            log.info(translate(
                'ExportToCSV', 'Empty dataset. Nothing to export.'))
            return

        # Scalar arrays aren't saved as CSV files
        if leaf.shape == ():
            log.info(translate(
                'ExportToCSV', 'Scalar array. Nothing to export.'))
            return

        # Datasets with more than 3 dimensions aren't saved as CSV files
        # (see module's docstring)
        if len(leaf.shape) > 3:
            log.info(translate(
                'ExportToCSV', 'The selected node has more than '
                '3 dimensions. I can\'t export it to CSV format.'))
            return

        # Variable lenght arrays aren't saved as CSV files
        if isinstance(leaf, tables.VLArray):
            log.info(translate(
                'ExportToCSV', 'The selected node is a VLArray. '
                'I can\'t export it to CSV format.'))
            return

        # Tables with Ndimensional fields aren't saved as CSV files
        is_table = isinstance(leaf, tables.Table)
        if is_table:
            if self._try_exporting_dataframe(leaf):
                return

            first_row = leaf[0]
            for item in first_row:
                if item.shape != ():
                    log.info(translate(
                        'ExportToCSV',
                        'Some fields aren\'t scalars. '
                        'I can\'t export the table to CSV format.'))
                    return

        # Get the required info for exporting the dataset
        export_info = self.getExportInfo(is_table)
        if export_info is None:
            return
        else:
            filepath, add_header = export_info

        try:
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            with open(filepath, 'ab') as out_handler:
                if add_header:
                    from functools import reduce
                    header = reduce(lambda x, y: '{0}, {1}'.format(x, y),
                                    leaf.colnames)
                    # To be consistent with numpy.savetxt use \n line breaks
                    out_handler.write(bytearray(header + '\n', 'UTF-8'))
                chunk_size = 10000
                nrows = leaf.nrows
                if chunk_size > nrows:
                    chunk_size = nrows
                # Behavior of np.divide in Python 2 and Python 3 is different so
                # we must explicitly ensure we get an integer
                nchunks = numpy.floor_divide(nrows, chunk_size)
                for i in numpy.arange(0, nchunks + 1):
                    QtWidgets.qApp.processEvents()
                    cstart = chunk_size * i
                    if cstart >= nrows:
                        break
                    cstop = cstart + chunk_size
                    if cstop > nrows:
                        cstop = nrows
                    numpy.savetxt(out_handler, leaf.read(cstart, cstop, 1),
                                  fmt='%s', delimiter=',')
        except OSError:
            vitables.utils.formatExceptionInfo()
        finally:
            QtWidgets.qApp.restoreOverrideCursor()
