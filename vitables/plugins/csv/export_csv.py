# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2010 Vicent Mas. All rights reserved
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

"""Plugin that provides export of datasets to files with CSV format.

When exporting tables, a header with the field names can be inserted.
"""

__docformat__ = 'restructuredtext'
_context = 'ExportToCSV'
__version__ = '0.5'
plugin_class = 'ExportToCSV'

import os

import tables
import numpy

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.vtSite import PLUGINSDIR


def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


class ExportToCSV(QtCore.QObject):
    """Provides CSV export capabilities for arrays.

    Some minor flaws: vlarrays with content other than ascii text cannot
    be exported.
    """

    def __init__(self):
        """The class constructor.
        """

        QtCore.QObject.__init__(self)

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()
        if self.vtapp is None:
            return

        # Add an entry under the Dataset menu
        self.addEntry()

        # Connect signals to slots
        self.vtapp.dataset_menu.aboutToShow.connect(self.updateDatasetMenu)


    def addEntry(self):
        """Add the Export to CSV... entry to menus.
        """

        icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(PLUGINSDIR, \
            'csv/icons/document-export.png'))
        icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)

        self.export_action = vitables.utils.createAction(self, 
            trs("E&xport to CSV...", "Save dataset as CSV"), 
            QtGui.QKeySequence.UnknownKey, self.export, 
            icon, 
            trs("Save the dataset as a plain text with CSV format", 
                "Status bar text for the Dataset -> Export to CSV... action"))

        # Add the action to the Dataset menu
        menu = self.vtapp.dataset_menu
        menu.addSeparator()
        menu.addAction(self.export_action)

        # Add the action to the leaf context menu
        cmenu = self.vtapp.leaf_node_cm
        cmenu.addSeparator()
        cmenu.addAction(self.export_action)


    def updateDatasetMenu(self):
        """Update the export QAction when the user pulls down the Dataset menu.

        This method is a slot. See class ctor for details.
        """

        enabled = True
        current = self.vtapp.dbs_tree_view.currentIndex()
        if current:
            leaf = self.vtapp.dbs_tree_model.nodeFromIndex(current)
            if leaf.node_kind in (u'group', u'root group'):
                enabled = False

        self.export_action.setEnabled(enabled)


    def getExportInfo(self, is_table):
        """Get info about the file where dataset will be stored.

        The retrieved info is the filepath and whether or not a header
        must be added.

        :Parameter `is_table`: is the exported dataset a tables.Table instance?
        """

        # Call the file selector (and, if needed, customise it)
        file_selector = vitables.utils.getFileSelector(\
            self.vtapp, 
            trs('Exporting dataset to CSV format', 
                'Caption of the Export to CSV dialog'), 
            dfilter=trs("""All Files (*)""", 
                'Filter for the Export to CSV dialog'), 
            settings={'accept_mode': QtGui.QFileDialog.AcceptSave, 
            'file_mode': QtGui.QFileDialog.AnyFile, 
            'history': self.vtapp.file_selector_history, 
            'label': trs('Export', 'Accept button text for QFileDialog')
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
                # Update the working directory
                working_dir = file_selector.directory().canonicalPath()
            else:  # Cancel clicked
                filepath = working_dir = QtCore.QString('')
        finally:
            add_header = False
            if is_table:
                add_header = header_cb.isChecked()
            del file_selector

        # Process the returned values
        filepath = unicode(filepath)
        working_dir = unicode(working_dir)

        if not filepath:
            # The user has canceled the dialog
            return

        # Update the history of the file selector widget
        self.vtapp.updateFSHistory(working_dir)

        # Check the returned path
        if os.path.exists(filepath):
            print trs(
                """\nWarning: """
                """export failed because destination file already exists.""",
                'A file creation error')
            return

        if os.path.isdir(filepath):
            print trs(
                """\nWarning: export failed """
                """because destination container is a directory.""",
                'A file creation error')
            return

        return filepath, add_header


    def export(self):
        """Export a given dataset to CSV format.

        This method is a slot connected to the `export` QAction. See the
        addEntry method for details.
        """

        # The PyTables node tied to the current leaf of the databases tree
        current = self.vtapp.dbs_tree_view.currentIndex()
        leaf = self.vtapp.dbs_tree_model.nodeFromIndex(current).node
        is_table = isinstance(leaf, tables.Table)

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
                header = reduce(lambda x, y: '%s, %s' % (x, y), leaf.colnames)
                # Ensure consistency with numpy.savetxt i.e. use \n line breaks
                out_handler.write(header + '\n')
            chunk_size = 10000
            stop = leaf.nrows
            div = numpy.divide(stop, chunk_size)
            for i in numpy.arange(0, div+1):
                QtGui.qApp.processEvents()
                cstart = chunk_size*i
                if cstart > stop:
                    cstart = stop
                cstop = cstart + chunk_size
                if cstop > stop:
                    cstop = stop
                numpy.savetxt(out_handler, 
                    leaf.read(start=cstart, stop=cstop), 
                    fmt='%s', delimiter=',')
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            out_handler.close()
            QtGui.qApp.restoreOverrideCursor()


    def helpAbout(self):
        """Brief description of the plugin."""

        # Text to be displayed
        about_text = trs(
            """<qt>
            <p>Plugin that provides export to CSV files capabilities.
            <p>Any kind of PyTables dataset can be exported. When 
            exporting tables, a header with the field names can be 
            inserted at top of the CSV file.
            </qt>""",
            'Text of an About plugin message box')

        descr = dict(module_name='export_csv.py', 
            folder=os.path.join(PLUGINSDIR, 'csv'), 
            version=__version__, 
            plugin_name='Export to CSV', 
            author='Vicent Mas <vmas@vitables.org>', 
            descr=about_text)

        return descr




