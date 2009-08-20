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
__version__ = '0.1'
plugin_class = 'ExportToCSV'

import os

import tables

import numpy

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import vitables.utils

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

        self.upgradeDatasetMenu()


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate(_context, source, comment))


    def upgradeDatasetMenu(self):
        """Add the Export to CSV... entry to the Dataset menu.
        """

        menu = self.vtapp.dataset_menu

        # Create the action
        action = QAction(menu)
        action.setText(self.__tr("E&xport to CSV...", "Save dataset as CSV"))
        action.setStatusTip(self.__tr("Save the dataset as a plain text with CSV format", 
            "Status bar text for the Dataset -> Export to CSV... action"))
        QObject.connect(action, SIGNAL("triggered()"), self.export)

        # Add the action to the Dataset menu
        menu.addSeparator()
        menu.addAction(action)


    def export(self):
        """Export a given dataset to CSV format.
        """

        current = self.vtapp.dbs_tree_view.currentIndex()
        # Locate the Leaf instance tied to the selected node
        dbs_tree_leaf = self.vtapp.dbs_tree_model.nodeFromIndex(current)
        leaf = dbs_tree_leaf.node # A PyTables node

        # Get a filename for the file where dataset will be stored
        dfilter = self.__tr("""All Files (*)""", 
            'Filter for the Export to CSV dialog')
        filename = self.vtapp.getFilepath(\
            self.__tr('Exporting dataset to CSV format', 
            'Caption of the Export to CSV dialog'),
            QFileDialog.AcceptSave, QFileDialog.AnyFile, dfilter=dfilter, 
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
                """\nWarning: """
                """export failed because destination container is a directory.""",
                'A file creation error')
            return

        # Everything seems OK so export the dataset
        try:
            numpy.savetxt(filename, leaf.read(), fmt='%s', delimiter=',')
        except:
            vitables.utils.formatExceptionInfo()




