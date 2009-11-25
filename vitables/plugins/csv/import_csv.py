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

#
#       Plugin Author: Jorge Ibáñez    -   jorge.ibannez@uam.es

"""Plugin that provides import of arrays and tables from CSV files.
"""

__docformat__ = 'restructuredtext'
_context = 'ImportCSV'
__version__ = '0.3'
plugin_class = 'ImportCSV'

import os

import tables
import numpy

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.vtSite import PLUGINSDIR

class ImportCSV(object):
    """Provides CSV import capabilities for tables and arrays.

    Some minor flaws: multidimensional fields are not well supported.
    They are imported as strings.
    """

    def __init__(self):
        """The class constructor.
        """

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()

        if self.vtapp is None:
            return

        self.dbt_model = self.vtapp.dbs_tree_model

        # Add an entry under the File menu
        self.addEntry()


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(QtGui.qApp.translate(_context, source, comment))


    def addEntry(self):
        """Add the Import CSV... entry to the File menu.
        """

        icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(PLUGINSDIR, \
            'csv/icons/document-import.png'))
        icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)

        self.import_submenu = \
            QtGui.QMenu(self.__tr('I&mport from CSV...','File -> Import CSV'))
        self.import_submenu.setSeparatorsCollapsible(False)
        self.import_submenu.setIcon(icon)

        # Create the actions
        self.import_table_action = vitables.utils.createAction(\
            self.import_submenu, 
            self.__tr("Import T&able...", \
                "Import table from CSV file"),
            QtGui.QKeySequence.UnknownKey, self.importTable,
            None,
            self.__tr("Import table from plain CSV file", 
            "Status bar text for the File -> Import CSV... -> Import Table"))

        self.import_array_action = vitables.utils.createAction(\
            self.import_submenu, 
            self.__tr("Import A&rray...", "Import array from CSV file"),
            QtGui.QKeySequence.UnknownKey, self.importArray,
            None,
            self.__tr("Import array from plain CSV file",
            "Status bar text for the File -> Import CSV... -> Import Array"))

        # Add the action to the Import submenu
        self.import_submenu.addAction(self.import_table_action)
        self.import_submenu.addAction(self.import_array_action)

        # Add submenu to file menu before the Close File action
        for item in self.vtapp.file_menu.actions():
            if item.objectName() == 'fileClose':
                self.vtapp.file_menu.insertMenu(item, self.import_submenu)
                self.vtapp.file_menu.insertSeparator(item)


    def isValidFilepath(self, filepath):
        """Check the filepath of the destination file.

        :Parameter `filepath`: the filepath where the imported dataset will live
        """

        valid = True
        if os.path.exists(filepath):
            print self.__tr(
                """\nWarning: """
                """export failed because destination file already exists.""",
                'A file creation error')
            valid = False

        elif os.path.isdir(filepath):
            print self.__tr(
                """\nWarning: export failed """
                """because destination container is a directory.""",
                'A file creation error')
            valid = False

        return valid


    def getSourceDest(self, leaf_kind):
        """Get the source CSV file and the destination PyTables file.

        :Parameter `leaf_kind`: the kind of container where data will be stored
        """

        # Get CSV filepath
        fs_args = {'accept_mode': QtGui.QFileDialog.AcceptOpen, 
            'file_mode': QtGui.QFileDialog.ExistingFile, 
            'history': self.vtapp.file_selector_history, 
            'label': self.__tr('Import', 'Accept button text for QFileDialog')}
        filepath, working_dir = vitables.utils.getFilepath(\
            self.vtapp, 
            self.__tr('Importing CSV file into %s',
                'Caption of the Import from CSV dialog') % leaf_kind, 
            dfilter=self.__tr("""CSV Files (*.csv);;"""
                """All Files (*)""", 'Filter for the Import from CSV dialog'), 
            settings=fs_args)

        if not filepath:
            # The user has canceled the dialog
            return None, None

        # Update the history of the file selector widget
        self.vtapp.updateFSHistory(working_dir)

        # Create the destination file
        try:
            dirname, filename = os.path.split(filepath)
            root = os.path.splitext(filename)[0]
            dest_filepath = os.path.join(dirname, '%s.h5' % root)
            if not self.isValidFilepath(dest_filepath):
                return None, None
            dbdoc = self.dbt_model.createDBDoc(dest_filepath)
        except:
            print self.__tr(
                """\nWarning: import failed """
                """because destination file cannot be created.""",
                'A file creation error')
            vitables.utils.formatExceptionInfo()
            return  None, None

        return filepath, dbdoc



    def importArray(self):
        """Import a plain CSV file into a tables.Array object.

        This is a slot method. See `addEntry` method for details.
        """

        leaf_kind = 'Array'
        filepath, dbdoc = self.getSourceDest(leaf_kind)
        if dbdoc is None:
            return

        # Import the CSV content
        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            # The dtypes are determined by the contents of each column
            # Multidimensional columns will have string datatype
            data = numpy.genfromtxt(filepath, delimiter=',', dtype=None)
            array_name = "imported_array"
            title = 'Imported from CSV file %s' % \
                os.path.basename(filepath)
            dbdoc.h5file.createArray(\
                '/', array_name, data, title=title)
            dbdoc.h5file.flush()
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            del data
            QtGui.qApp.restoreOverrideCursor()


    def importTable(self):
        """Import a plain CSV file into a tables.Table object.

        This is a slot method. See `addEntry` method for details.
        """

        leaf_kind = 'Table'
        filepath, dbdoc = self.getSourceDest(leaf_kind)
        if dbdoc is None:
            return

        # Import the CSV content
        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            data = numpy.genfromtxt(filepath, delimiter=',', names=None, 
                dtype=None)
            if data.dtype.fields is None:
                # Data is a homogeneous dataset
                descr = dict([('f%s' % f, tables.Col.from_dtype(data.dtype)) \
                    for f in range(0, data.shape[1])])
            else:
                # Data is a heterogeneous dataset
                descr = dict([(f, tables.Col.from_dtype(t[0])) for f, t in 
                    data.dtype.fields.items()])
            table_name = "imported_table"
            title = 'Imported from CSV file %s' % \
                os.path.basename(filepath)
            table = dbdoc.h5file.createTable(\
                '/', table_name, descr, title=title)
            #Fill table with data
            table.append(data)
            table.flush()
            dbdoc.h5file.flush()
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            del data
            QtGui.qApp.restoreOverrideCursor()

