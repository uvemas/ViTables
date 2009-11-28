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
import tempfile

import tables
import numpy

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.vtSite import PLUGINSDIR



def arrayInfo(input_handler, kind):
    """Return the useful information about the array being created.

    :Parameters:
    - `input_handler`: the file handler of the inspected file
    - `kind`: the kind of array being created
    """

    # Inspect the CSV file reading its first line
    # The dtypes are determined by the contents of each column
    # Multidimensional columns will have string datatype
    temp_file = tempfile.TemporaryFile()
    line = input_handler.readline()
    temp_file.writelines(line)
    temp_file.seek(0)
    data = numpy.genfromtxt(temp_file, delimiter=',', dtype=None)
    temp_file.close()

    # Our counting algorithm is faster than looping over lines with
    # fh.readline and incrementing a counter at every step
    lines = 0
    itemsize = 0
    buf_size = 1024 * 1024
    read_fh = input_handler.read
    input_handler.seek(0)

    if data.dtype.name.startswith('string'):
        # Count lines and find out the biggest itemsize
        buf = read_fh(buf_size)
        while buf:
            temp_file = tempfile.TemporaryFile()
            temp_file.writelines(buf)
            temp_file.seek(0)
            idata = numpy.genfromtxt(temp_file, delimiter=',', dtype=None)
            itemsize = max(itemsize, idata.dtype.itemsize)
            temp_file.close()
            del idata
            lines += buf.count('\n')
            buf = read_fh(buf_size)
    else:
        # Count lines
        buf = read_fh(buf_size)
        while buf:
            lines += buf.count('\n')
            buf = read_fh(buf_size)

    if itemsize:
        atom = tables.StringAtom(itemsize)
    else:
        atom = tables.Atom.from_dtype(data.dtype)

    # Get the data shape
    if lines == 1:
        # Corner case: the file only has one row
        if kind == 'CArray':
            array_shape = data.shape
        elif kind == 'EArray':
            array_shape = (0, )
        lines = data.shape[0]
    elif data.shape == ():
        # Corner case: the file has just one column
        if kind == 'CArray':
            array_shape = (lines, )
        elif kind == 'EArray':
            array_shape = (0, )
    else:
        # General case: the file is a MxN array
        if kind == 'CArray':
            array_shape = (lines, data.shape[0])
        elif kind == 'EArray':
            array_shape = (0, data.shape[0])

    del data
    input_handler.seek(0)
    return lines, atom, array_shape


def tableInfo(input_handler):
    """Return the useful information about the table being created.

    :Parameters:
    - `input_handler`: the file handler of the inspected file
    """

    # Inspect the CSV file reading its first line
    # The dtypes are determined by the contents of each column
    # Multidimensional columns will have string datatype
    temp_file = tempfile.TemporaryFile()
    line = input_handler.readline()
    temp_file.writelines(line)
    temp_file.seek(0)
    data = numpy.genfromtxt(temp_file, delimiter=',', dtype=None)
    temp_file.close()

    if data.dtype.fields is None:
        # data is a homogeneous array
        return homogeneousTableInfo(input_handler, data)
    else:
        # data is a heterogeneous dataset
        return heterogeneousTableInfo(input_handler, data)


def homogeneousTableInfo(input_handler, data):
    """Return the useful information about the table being created.

    The `data` array is homegenous, i.e. all fields have the same dtype.

    :Parameters:
    - `input_handler`: the file handler of the inspected CSV file
    - `data`: a numpy array which contains the first line of the CSV file
    """

    # Our counting algorithm is faster than looping over lines with
    # fh.readline and incrementing a counter at every step
    lines = 0
    buf_size = 1024 * 1024
    read_fh = input_handler.read
    input_handler.seek(0)

    # Count lines and, if dtype is a string, find out the biggest itemsize
    buf = read_fh(buf_size)
    if data.dtype.name.startswith('string'):
        itemsize = 0
        while buf:
            temp_file = tempfile.TemporaryFile()
            temp_file.writelines(buf)
            temp_file.seek(0)
            idata = numpy.genfromtxt(temp_file, delimiter=',', dtype=None)
            itemsize = max(itemsize, idata.dtype.itemsize)
            del idata
            temp_file.close()
            lines += buf.count('\n')
            buf = read_fh(buf_size)
    else:
        while buf:
            lines += buf.count('\n')
            buf = read_fh(buf_size)

    if data.shape:
        # CSV file has more than one field
        data_fields = range(0, data.shape[0])
    else:
        # CSV file has just one field
        data_fields = [0]

    if data.dtype.name.startswith('string'):
        descr = dict([('f%s' % field, tables.StringCol(itemsize)) \
            for field in data_fields])
    else:
        descr = dict([('f%s' % field, tables.Col.from_dtype(data.dtype)) \
            for field in data_fields])

    del data
    return (lines, descr)


def heterogeneousTableInfo(input_handler, data):
    """Return the useful information about the table being created.

    The `data` array is heterogenous, i.e. not all fields have the same
    dtype.

    :Parameters:
    - `input_handler`: the file handler of the inspected CSV file
    - `data`: a numpy array which contains the first line of the CSV file
    """

    # Our counting algorithm is faster than looping over lines with
    # fh.readline and incrementing a counter at every step
    lines = 0
    buf_size = 1024 * 1024
    read_fh = input_handler.read
    input_handler.seek(0)

    # Stuff used for finding out itemsizes of string fields
    itemsizes = {}
    for field in range(0, len(data.dtype)):
        if data.dtype[field].name.startswith('string'):
            itemsizes[field] = 0

    # Count lines and, if a dtype is a string, find out its biggest itemsize
    buf = read_fh(buf_size)
    if itemsizes:
        while buf:
            temp_file = tempfile.TemporaryFile()
            temp_file.writelines(buf)
            for field in itemsizes.keys():
                temp_file.seek(0)
                idata = numpy.genfromtxt(temp_file, delimiter=',', 
                    usecols=(field,), dtype=None)
                itemsizes[field] = \
                    max(itemsizes[field], idata.dtype.itemsize)
                del idata
            temp_file.close()
            lines += buf.count('\n')
            buf = read_fh(buf_size)
    else:
        while buf:
            lines += buf.count('\n')
            buf = read_fh(buf_size)

    descr = dict([(f, tables.Col.from_dtype(t[0])) for f, t in 
        data.dtype.fields.items()])
    for field in itemsizes:
        descr['f%s' % field] = tables.StringCol(itemsizes[field])

    del data
    return (lines, descr)
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
        actions = {}
        actions['import_table'] = vitables.utils.createAction(\
            self.import_submenu, 
            self.__tr("Import T&able...", \
                "Import table from CSV file"),
            QtGui.QKeySequence.UnknownKey, self.importTable,
            None,
            self.__tr("Import Table from plain CSV file", 
            "Status bar text for the File -> Import CSV... -> Import Table"))

        actions['import_array'] = vitables.utils.createAction(\
            self.import_submenu, 
            self.__tr("Import A&rray...", "Import array from CSV file"),
            QtGui.QKeySequence.UnknownKey, self.importArray,
            None,
            self.__tr("Import Array from plain CSV file",
            "Status bar text for the File -> Import CSV... -> Import Array"))

        actions['import_carray'] = vitables.utils.createAction(\
            self.import_submenu, 
            self.__tr("Import C&Array...", "Import carray from CSV file"),
            QtGui.QKeySequence.UnknownKey, self.importCArray,
            None,
            self.__tr("Import CArray from plain CSV file",
            "Status bar text for the File -> Import CSV... -> Import CArray"))

        actions['import_earray'] = vitables.utils.createAction(\
            self.import_submenu, 
            self.__tr("Import E&Array...", "Import earray from CSV file"),
            QtGui.QKeySequence.UnknownKey, self.importEArray,
            None,
            self.__tr("Import EArray from plain CSV file",
            "Status bar text for the File -> Import CSV... -> Import EArray"))

        # Add actions to the Import submenu
        keys = ('import_table', 'import_array', 'import_carray', 
            'import_earray')
        vitables.utils.addActions(self.import_submenu, keys, actions)

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



    def importDataset(self, kind):
        """Import a plain CSV file into a tables.Array object.

        :Parameter `kind`: the kind of array to be created (EArray, CArray)
        """

        filepath, dbdoc = self.getSourceDest(kind)
        if dbdoc is None:
            return

        # Import the CSV content
        try:
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            chunk_size = 10000
            input_handler = open(filepath, 'r+')
            if kind == 'Table':
                (stop, descr) = tableInfo(input_handler)
            else:
                (stop, atom, array_shape) = \
                    arrayInfo(input_handler, kind)

            # Create the dataset
            io_filters = tables.Filters(complevel=9, complib='lzo')
            dataset_name = "imported_%s" % kind
            atitle = 'Source CSV file %s' % \
                os.path.basename(filepath)
            if kind == 'CArray':
                dataset = dbdoc.h5file.createCArray('/', dataset_name, atom, 
                    array_shape, title=atitle, filters=io_filters)
            elif kind == 'EArray':
                dataset = dbdoc.h5file.createEArray('/', dataset_name, atom, 
                    array_shape, title=atitle, filters=io_filters, 
                    expectedrows=stop)
            elif kind == 'Table':
                dataset = dbdoc.h5file.createTable(\
                    '/', dataset_name, descr, title=atitle)

            # Fill the dataset in a memory effcient way
            input_handler.seek(0)
            div = numpy.divide(stop, chunk_size)
            for i in numpy.arange(0, div+1):
                QtGui.qApp.processEvents()
                cstart = chunk_size*i
                if cstart > stop:
                    cstart = stop
                cstop = cstart + chunk_size
                if cstop > stop:
                    cstop = stop
                # Fill a intermediate buffer of small size in order to 
                # save memory when csv file is very large
                temp_file = tempfile.TemporaryFile()
                for i in range(cstart, cstop - cstart):
                    line = input_handler.readline()
                    temp_file.writelines(line)
                temp_file.seek(0)
                data = numpy.genfromtxt(temp_file, delimiter=',', dtype=None)
                temp_file.close()

                # Append data to the dataset
                if kind == 'CArray':
                    dataset[cstart:cstop] = data
                elif kind == 'EArray':
                    dataset.append(data)
                elif kind == 'Table':
                    dataset.append(data)
                dataset.flush()
                del data
            dbdoc.h5file.flush()
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtGui.qApp.restoreOverrideCursor()
            input_handler.close()


    def importCArray(self):
        """Import a plain CSV file into a tables.CArray object.

        This is a slot method. See `addEntry` method for details.
        """
        self.importDataset('CArray')


    def importEArray(self):
        """Import a plain CSV file into a tables.EArray object.

        This is a slot method. See `addEntry` method for details.
        """
        self.importDataset('EArray')


    def importTable(self):
        """Import a plain CSV file into a tables.Table object.

        This is a slot method. See `addEntry` method for details.
        """
        self.importDataset('Table')


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

            # Create the array
            array_name = "imported_Array"
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
