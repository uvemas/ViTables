# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008, 2009 Vicent Mas. All rights reserved
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

"""Plugin that provides export of arrays to files with CSV format.
"""

__docformat__ = 'restructuredtext'
_context = 'ExportToCSV'
__version__ = '0.3'
plugin_class = 'ExportToCSV'

import os

import numpy

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.vtSite import PLUGINSDIR

class ExportToCSV(object):
    """Provides CSV export capabilities for arrays.

    Some minor flaws: vlarrays with content other than ascii text cannot
    be exported.
    """

    def __init__(self):
        """The class constructor.
        """

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()
        if self.vtapp is None:
            return

        self.addEntry()

        # Connect signals to slots
        QtCore.QObject.connect(self.vtapp.dataset_menu, 
            QtCore.SIGNAL('aboutToShow()'), 
            self.updateDatasetMenu)


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(QtGui.qApp.translate(_context, source, comment))


    def addEntry(self):
        """Add the Export to CSV... entry to the Dataset menu.
        """

        menu = self.vtapp.dataset_menu

        icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(PLUGINSDIR, \
            'csv/icons/document-export.png'))
        icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)

        self.export_action = vitables.utils.createAction(menu, 
            self.__tr("E&xport to CSV...", "Save dataset as CSV"), 
            QtGui.QKeySequence.UnknownKey, self.export, 
            icon, 
            self.__tr("Save the dataset as a plain text with CSV format", 
                "Status bar text for the Dataset -> Export to CSV... action"))

        # Add the action to the Dataset menu
        menu.addSeparator()
        menu.addAction(self.export_action)




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


    def export(self):
        """Export a given dataset to CSV format.

        This method is a slot connected to the `export` QAction. See the
        addEntry method for details.
        """

        # The PyTables node tied to the current leaf of the databases tree
        current = self.vtapp.dbs_tree_view.currentIndex()
        leaf = self.vtapp.dbs_tree_model.nodeFromIndex(current).node

        # Get a filename for the file where dataset will be stored
        dfilter = self.__tr("""All Files (*)""", 
            'Filter for the Export to CSV dialog')
        filename = self.vtapp.getFilepath(\
            self.__tr('Exporting dataset to CSV format', 
            'Caption of the Export to CSV dialog'),
            QtGui.QFileDialog.AcceptSave, 
            QtGui.QFileDialog.AnyFile, 
            dfilter=dfilter, 
            label='Export')

        if not filename:
            # The user has canceled the dialog
            return

        # Check the returned path
        if os.path.exists(filename):
            print self.__tr(
                """\nWarning: """
                """export failed because destination file already exists.""",
                'A file creation error')
            return
        if os.path.isdir(filename):
            print self.__tr(
                """\nWarning: export failed """
                """because destination container is a directory.""",
                'A file creation error')
            return

        # Everything seems OK so export the dataset
        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            out_handler = open(filename, 'w')
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




