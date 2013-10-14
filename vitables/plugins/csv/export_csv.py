#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       Copyright (C) 2008-2013 Vicent Mas. All rights reserved
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
"""


__docformat__ = 'restructuredtext'
__version__ = '0.7'
plugin_class = 'ExportToCSV'
plugin_name = 'CSV exporter'
comment = 'Export datasets to CSV files.'

import os
import re

import tables
import numpy

from PyQt4 import QtCore
from PyQt4 import QtGui

import vitables.utils
import vitables.plugin_utils
from vitables.vtsite import PLUGINSDIR
from vitables.plugins.csv.aboutpage import AboutPage

translate = QtGui.QApplication.translate


def checkFilenameExtension(filepath):
    """
    Check the filename extension of the CSV file.

    If the filename has no extension this method adds .csv
    extension to it.

    :Parameter filepath: the full path of the file

    :Returns: the filepath with the proper extension
    """

    if not re.search('\.(.+)$', os.path.basename(filepath)):
        ext = '.csv'
        filepath = filepath + ext
    return filepath


class ExportToCSV(QtCore.QObject):
    """Provides `CSV` export capabilities for arrays.

    Some minor flaws: `tables.VLArray` nodes can't be exported. Neither can 
    ``numpy`` scalar arrays.
    """

    def __init__(self):
        """The class constructor.
        """

        super(ExportToCSV, self).__init__()

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()
        if self.vtapp is None:
            return

        self.vtgui = vitables.plugin_utils.getVTGui()

        # Add an entry under the Dataset menu
        self.addEntry()

        # Connect signals to slots
        self.vtgui.dataset_menu.aboutToShow.connect(self.updateDatasetMenu)
        self.vtgui.leaf_node_cm.aboutToShow.connect(self.updateDatasetMenu)


    def addEntry(self):
        """Add the `Export to CSV..`. entry to `Dataset` menu.
        """

        export_icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(PLUGINSDIR, \
            'csv/icons/document-export.png'))
        export_icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)

        self.export_action = QtGui.QAction(
            translate('ExportToCSV', 
                "E&xport to CSV...", 
                "Save dataset as CSV"), 
            self, 
            shortcut=QtGui.QKeySequence.UnknownKey, triggered=self.export, 
            icon=export_icon, 
            statusTip=translate('ExportToCSV', 
                "Save the dataset as a plain text with CSV format", 
                "Status bar text for the Dataset -> Export to CSV... action"))

        # Add the action to the Dataset menu
        vitables.plugin_utils.addToMenu(self.vtgui.dataset_menu,
            self.export_action)

        # Add the action to the leaf context menu
        vitables.plugin_utils.addToLeafContextMenu(self.export_action)


    def updateDatasetMenu(self):
        """Update the `export` QAction when the Dataset menu is pulled down.

        This method is a slot. See class ctor for details.
        """

        enabled = True
        current = self.vtgui.dbs_tree_view.currentIndex()
        if current:
            leaf = self.vtgui.dbs_tree_model.nodeFromIndex(current)
            if leaf.node_kind in (u'group', u'root group'):
                enabled = False

        self.export_action.setEnabled(enabled)


    def getExportInfo(self, is_table):
        """Get info about the file where dataset will be stored.

        The retrieved info is the filepath and whether or not a header
        must be added.

        :Parameter is_table: True if the exported dataset is a tables.Table 
          instance
        """

        # Call the file selector (and, if needed, customise it)
        file_selector = vitables.utils.getFileSelector(\
            self.vtgui, 
            translate('ExportToCSV', 'Exporting dataset to CSV format', 
                'Caption of the Export to CSV dialog'), 
            dfilter=translate('ExportToCSV', """CSV Files (*.csv);;"""
                """All Files (*)""", 'Filter for the Export to CSV dialog'), 
            settings={'accept_mode': QtGui.QFileDialog.AcceptSave, 
            'file_mode': QtGui.QFileDialog.AnyFile, 
            'history': self.vtapp.file_selector_history, 
            'label': translate('ExportToCSV', 'Export', 
                'Accept button text for QFileDialog')
            })

        # Customise the file selector dialog for exporting to CSV files
        if is_table:
            fs_layout = file_selector.layout()
            header_label = QtGui.QLabel('Add header:', file_selector)
            header_cb = QtGui.QCheckBox(file_selector)
            fs_layout.addWidget(header_label, 4, 0)
            fs_layout.addWidget(header_cb, 4, 1)

        # Execute the dialog
        try:
            if file_selector.exec_():  # OK clicked
                filepath = file_selector.selectedFiles()[0]
                # Make sure filepath contains no backslashes
                filepath = QtCore.QDir.fromNativeSeparators(filepath)
                filepath = checkFilenameExtension(filepath)
                # Update the working directory
                working_dir = file_selector.directory().canonicalPath()
            else:  # Cancel clicked
                filepath = working_dir = u''
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
            print(translate('ExportToCSV', 
                """\nWarning: """
                """export failed because destination file already exists.""",
                'A file creation error'))
            return

        if os.path.isdir(filepath):
            print(translate('ExportToCSV', 
                """\nWarning: export failed """
                """because destination container is a directory.""",
                'A file creation error'))
            return

        return filepath, add_header


    def export(self):
        """Export a given dataset to a `CSV` file.

        This method is a slot connected to the `export` QAction. See the
        :meth:`addEntry` method for details.
        """

        # The PyTables node tied to the current leaf of the databases tree
        current = self.vtgui.dbs_tree_view.currentIndex()
        leaf = self.vtgui.dbs_tree_model.nodeFromIndex(current).node

        # Empty datasets can't be saved as CSV files
        if leaf.nrows == 0:
            print(translate('ExportToCSV', 
                "\nWarning: Empty dataset. Nothing to export."))
            return

        # Scalar arrays can't be saved as CSV files
        if leaf.shape == ():
            print(translate('ExportToCSV', 
                "\nWarning: Scalar array. Nothing to export."))
            return

        # Datasets with more than 2 dimensions can't be saved as CSV files
        if len(leaf.shape) > 2:
            print(translate('ExportToCSV', 
                """\nWarning: The selected node has more than """
                """2 dimensions. I can't export it to CSV format."""))
            return

        # Variable lenght arrays can't be saved as CSV files
        if isinstance(leaf, tables.VLArray):
            print(translate('ExportToCSV', 
                """\nWarning: The selected node is a VLArray. """
                """I can't export it to CSV format."""))
            return

        # Tables with Ndimensional fields can't be saved as CSV files
        is_table = isinstance(leaf, tables.Table)
        if is_table:
            first_row = leaf[0]
            for item in first_row:
                if item.shape != ():
                    print(translate('ExportToCSV', 
                        """\nWarning: Some fields aren't scalars """
                        """I can't export the table to CSV format."""))
                    return

        # Get the required info for exporting the dataset
        export_info = self.getExportInfo(is_table)
        if export_info is None:
            return
        else:
            filepath, add_header = export_info

        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            out_handler = open(filepath, 'w')
            if add_header:
                header = \
                    reduce(lambda x, y: u'{0}, {1}'.format(x, y), leaf.colnames)
                # Ensure consistency with numpy.savetxt i.e. use \n line breaks
                out_handler.write(header + '\n')
            chunk_size = 10000
            nrows = leaf.nrows
            if chunk_size > nrows:
                chunk_size = nrows
            nchunks = numpy.divide(nrows, chunk_size)
            for i in numpy.arange(0, nchunks+1):
                QtGui.qApp.processEvents()
                cstart = chunk_size*i
                if cstart >= nrows:
                    break
                cstop = cstart + chunk_size
                if cstop > nrows:
                    cstop = nrows
                numpy.savetxt(out_handler, 
                    leaf.read(cstart, cstop), 
                    fmt='%s', delimiter=',')
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            out_handler.close()
            QtGui.qApp.restoreOverrideCursor()


    def helpAbout(self, parent):
        """Full description of the plugin.

        This is a convenience method which works as expected by
        :meth:preferences.preferences.Preferences.aboutPluginPage i.e.
        build a page which contains the full description of the plugin
        and, optionally, allows for its configuration.

        :Parameter about_page: the container widget for the page
        """

        # Plugin full description
        desc = {'version': __version__, 
            'module_name': os.path.join(os.path.basename(__file__)), 
            'folder': os.path.join(os.path.dirname(__file__)), 
            'author': 'Vicent Mas <vmas@vitables.org>', 
            'about_text': translate('ExportToCSV', 
            """<qt>
            <p>Plugin that provides export to CSV files capabilities.
            <p>Any kind of PyTables dataset can be exported. When 
            exporting tables, a header with the field names can be 
            inserted at top of the CSV file.
            </qt>""",
            'Text of an About plugin message box')}
        about_page = AboutPage(desc, parent)
        return about_page
