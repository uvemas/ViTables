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

#
# Plugin initial draft author: Jorge Ibanez jorge.ibannez@uam.es
#

"""Plugin that provides import of arrays and tables from CSV files.

The pipeline for importing a CSV file is:

CSV file --> numpy array --> tables.Leaf

The numpy array is created via numpy.genfromtxt. The tables.Leaf instance
is created using the apropriate constructors.

Beware that importing big files is a slow process because the whole file
has to be read from disk, transformed and write back to disk again so
there is a lot of disk IO.

Other aspects to take into account:

- creation of tables.Array datasets requires the numpy array containing the
  whole CSV file to be loaded in memory. If the file is large enough you can
  run out of memory.

- creation of tables.CArray datasets requires an additional parsing of the
  whole CSV file in order to find out its number of rows (it is a required
  argument of the CArray constructor)

- there is a penalty performance when string dtypes are involved. The reason
  is that string fields use to have variable length so, before the numpy
  array is created, we need to find out the minimum itemsize required for
  storing those string fields with no lose of data. This step requires an
  additional parsing of the whole CSV file.
"""

__docformat__ = 'restructuredtext'
_context = 'ImportCSV'
__version__ = '0.8'
plugin_class = 'ImportCSV'

import os
import tempfile

import tables
import numpy

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.vtSite import PLUGINSDIR


def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


def getArray(buf):
    """Fill an intermediate numpy array with data read from the CSV file.

    The dtypes are determined by the contents of each column.
    Multidimensional columns will have string datatype.

    :Parameter `buf`: the data buffer
    """

    # The dtypes are determined by the contents of each column
    # Multidimensional columns will have string datatype
    temp_file = tempfile.TemporaryFile()
    temp_file.writelines(buf)
    temp_file.seek(0)
    data = numpy.genfromtxt(temp_file, delimiter=',', dtype=None)
    temp_file.close()
    return data


def tableInfo(input_handler):
    """Return the useful information about the Table being created.

    :Parameters:
    - `input_handler`: the file handler of the inspected file    
    """

    # Inspect the CSV file reading its second line
    # (reading the first line is not safe as it could be a header)
    input_handler.seek(0)
    first_line = getArray(input_handler.readline())
    try:
        data = getArray(input_handler.readline())
    except IOError:
        # The second line cannot be read. We assume there is only on line
        data = first_line

    # Estimate the number of rows of the file
    filesize = os.path.getsize(input_handler.name)
    record_size = data.size * data.itemsize
    nrows = filesize/record_size

    if data.dtype.fields is None:
        # data is a homogeneous array
        descr, has_header = \
            homogeneousTableInfo(input_handler, first_line, data)
    else:
        # data is a heterogeneous dataset
        descr, has_header = \
            heterogeneousTableInfo(input_handler, first_line, data)

    del data
    return (nrows, descr, has_header)


def heterogeneousTableInfo(input_handler, first_line, data):
    """Return the useful information about the table being created.

    The `data` array is heterogenous, i.e. not all fields have the same
    dtype.

    :Parameters:
    - `input_handler`: the file handler of the inspected CSV file
    - `first_line`: a numpy array which contains the first line of the CSV 
                    file
    - `data`: a numpy array which contains the second line of the CSV file
    """

    has_header = False
    if first_line.dtype.name.startswith('string'):
        has_header = True

    # Stuff used for finding out itemsizes of string fields
    itemsizes = {}
    for field in range(0, len(data.dtype)):
        if data.dtype[field].name.startswith('string'):
            itemsizes[field] = 0

    # If a dtype is a string, find out its biggest itemsize
    if itemsizes:
        buf_size = 1024 * 1024
        read_fh = input_handler.readlines
        input_handler.seek(0)
        if has_header:
            # Skip the header
            input_handler.readline()
        buf = read_fh(buf_size)
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
            buf = read_fh(buf_size)

    if has_header:
        descr = {}
        for i in range(0, first_line.size):
            dtype = data.dtype.fields['f%s'%i][0]
            descr[first_line[i]] = tables.Col.from_dtype(dtype, pos=i)
        for i in itemsizes:
            descr[first_line[i]] = tables.StringCol(itemsizes[i], pos=i)
    else:
        descr = dict([(f, tables.Col.from_dtype(t[0])) for f, t in 
            data.dtype.fields.items()])
        for i in itemsizes:
            descr['f%s'%i] = tables.StringCol(itemsizes[i])

    return descr, has_header


def homogeneousTableInfo(input_handler, first_line, data):
    """Return the useful information about the table being created.

    The `data` array is homegenous, i.e. all fields have the same dtype.

    :Parameters:
    - `input_handler`: the file handler of the inspected CSV file
    - `first_line`: a numpy array which contains the first line of the CSV 
                    file
    - `data`: a numpy array which contains the second line of the CSV file
    """

    has_header = False
    # If dtype is a string,  ask to user if the table has a header or not.
    # Then find out the biggest itemsize
    if data.dtype.name.startswith('string'):
        answer = askForHelp(first_line)
        buf_size = 1024 * 1024
        read_fh = input_handler.readlines
        input_handler.seek(0)
        if answer == 'Header':
            # Skip the header
            has_header = True
            input_handler.readline()
        itemsize = 0
        buf = read_fh(buf_size)
        if not buf:
            # If the CSV file contains just one line
            itemsize = first_line.dtype.itemsize
        while buf:
            temp_file = tempfile.TemporaryFile()
            temp_file.writelines(buf)
            temp_file.seek(0)
            idata = numpy.genfromtxt(temp_file, delimiter=',', dtype=None)
            itemsize = max(itemsize, idata.dtype.itemsize)
            del idata
            temp_file.close()
            buf = read_fh(buf_size)
    elif first_line.dtype.name.startswith('string'):
        has_header = True

    # Iterate over the data fields and make the table description
    # If the CSV file contains just one field then first_line is a
    # scalar array and cannot be iterated so we reshape it
    if first_line.shape == ():
        first_line = first_line.reshape(1,)
    indices = range(0, first_line.shape[0])

    if has_header:
        if data.dtype.name.startswith('string'):
            descr = dict([(first_line[i], 
                tables.StringCol(itemsize, pos=i)) for i in indices])
        else:
            descr = dict([(first_line[i], 
                tables.Col.from_dtype(data.dtype, pos=i)) for i in indices])
    else:
        if data.dtype.name.startswith('string'):
            descr = dict([('f%s' % field, tables.StringCol(itemsize)) \
                for field in indices])
        else:
            descr = dict([('f%s' % field, tables.Col.from_dtype(data.dtype)) \
                for field in indices])

    return descr, has_header


def askForHelp(first_line):
    """Ask to user if the first row is a header.

    :Parameter `first_line`: a numpy array which contains the first line of 
                             the CSVfile
    """

    title = trs('Resolving first line role', 'Message box title')
    text = trs("""Does the first line of the file contain """
        """a table header or regular data?""", 'Message box text')
    itext = ''
    try:
        dtext = reduce(lambda x, y: '%s, %s' % (x, y), first_line)
    except TypeError:
        # If first_line has only one field reduce raises a TypeError
        dtext = first_line.tostring()
    buttons = {\
        'Header': (trs('Header', 'Button text'), QtGui.QMessageBox.YesRole), 
        'Data': (trs('Data', 'Button text'), QtGui.QMessageBox.NoRole),
        }
    return vitables.utils.questionBox(title, text, itext, dtext, buttons)


def earrayInfo(input_handler):
    """Return the useful information about the EArray being created.

    :Parameters:
    - `input_handler`: the file handler of the inspected file
    """

    # Inspect the CSV file reading its first line
    # The dtypes are determined by the contents of each column
    # Multidimensional columns will have string datatype
    data = getArray(input_handler.readline())

    # Estimate the number of rows of the file
    filesize = os.path.getsize(input_handler.name)
    record_size = data.size * data.itemsize
    nrows = filesize/record_size

    if data.dtype.name.startswith('string'):
        # Find out the biggest itemsize
        itemsize = 0
        buf_size = 1024 * 1024
        read_fh = input_handler.readlines
        input_handler.seek(0)
        buf = read_fh(buf_size)
        while buf:
            temp_file = tempfile.TemporaryFile()
            temp_file.writelines(buf)
            temp_file.seek(0)
            idata = numpy.genfromtxt(temp_file, delimiter=',', dtype=None)
            itemsize = max(itemsize, idata.dtype.itemsize)
            temp_file.close()
            del idata
            buf = read_fh(buf_size)
        atom = tables.StringAtom(itemsize)
    else:
        # With compound dtypes this will raise a ValueError
        atom = tables.Atom.from_dtype(data.dtype)

    # Get the data shape
    if nrows < 2:
        # Corner case: the file only has one row
        array_shape = (0, )
    elif data.shape == ():
        # Corner case: the file has just one column
        array_shape = (0, )
    else:
        # General case: the file is a MxN array
        array_shape = (0, data.shape[0])

    del data
    input_handler.seek(0)
    return nrows, atom, array_shape


def carrayInfo(input_handler):
    """Return the useful information about the CArray being created.

    :Parameters:
    - `input_handler`: the file handler of the inspected file
    """

    # Inspect the CSV file reading its first line
    # The dtypes are determined by the contents of each column
    # Multidimensional columns will have string datatype
    data = getArray(input_handler.readline())

    # This counting algorithm is faster than looping over lines with
    # fh.readline and incrementing a counter at every step
    lines = 0
    itemsize = 0
    buf_size = 1024 * 1024
    read_fh = input_handler.readlines
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
            lines += len(buf)
            buf = read_fh(buf_size)
    else:
        # Count lines
        buf = read_fh(buf_size)
        while buf:
            lines += len(buf)
            buf = read_fh(buf_size)

    if itemsize:
        atom = tables.StringAtom(itemsize)
    else:
        atom = tables.Atom.from_dtype(data.dtype)

    # Get the data shape
    if lines == 1:
        # Corner case: the file only has one row
        array_shape = data.shape
        lines = data.shape[0]
    elif data.shape == ():
        # Corner case: the file has just one column
        array_shape = (lines, )
    else:
        # General case: the file is a MxN array
        array_shape = (lines, data.shape[0])

    del data
    input_handler.seek(0)
    return atom, array_shape


def isValidFilepath(filepath):
    """Check the filepath of the destination file.

    :Parameter `filepath`: the filepath where the imported dataset will live
    """


    valid = True
    if os.path.exists(filepath):
        print trs(
            """\nWarning: """
            """import failed because destination file already exists.""",
            'A file creation error')
        valid = False

    elif os.path.isdir(filepath):
        print trs(
            """\nWarning: import failed """
            """because destination container is a directory.""",
            'A file creation error')
        valid = False

    return valid


class ImportCSV(QtCore.QObject):
    """Provides CSV import capabilities for tables and arrays.

    Some minor flaws: multidimensional fields are not well supported.
    They are imported as strings.
    """

    def __init__(self):
        """The class constructor.
        """

        QtCore.QObject.__init__(self)

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()
        self.vtgui = self.vtapp.gui

        if self.vtapp is None:
            return

        self.dbt_model = self.vtgui.dbs_tree_model

        # Add an entry under the File menu
        self.addEntry()


    def addEntry(self):
        """Add the Import CSV... entry to the menus.
        """

        icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(PLUGINSDIR, \
            'csv/icons/document-import.png'))
        icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)

        self.import_submenu = \
            QtGui.QMenu(trs('I&mport from CSV...','File -> Import CSV'))
        self.import_submenu.setSeparatorsCollapsible(False)
        self.import_submenu.setIcon(icon)

        # Create the actions
        actions = {}
        actions['import_table'] = QtGui.QAction(
            trs("Import T&able...", "Import table from CSV file"), self, 
            shortcut=QtGui.QKeySequence.UnknownKey, 
            triggered=self.importTable, 
            statusTip=trs("Import Table from plain CSV file", 
            "Status bar text for the File -> Import CSV... -> Import Table"))

        actions['import_array'] = QtGui.QAction(
            trs("Import A&rray...", "Import array from CSV file"), self, 
            shortcut=QtGui.QKeySequence.UnknownKey, 
            triggered=self.importArray, 
            statusTip=trs("Import Array from plain CSV file",
            "Status bar text for the File -> Import CSV... -> Import Array"))

        actions['import_carray'] = QtGui.QAction(
            trs("Import C&Array...", "Import carray from CSV file"), self, 
            shortcut=QtGui.QKeySequence.UnknownKey, 
            triggered=self.importCArray, 
            statusTip=trs("Import CArray from plain CSV file",
            "Status bar text for the File -> Import CSV... -> Import CArray"))

        actions['import_earray'] = QtGui.QAction(
            trs("Import E&Array...", "Import earray from CSV file"), self, 
            shortcut=QtGui.QKeySequence.UnknownKey, 
            triggered=self.importEArray,
            statusTip=trs("Import EArray from plain CSV file",
            "Status bar text for the File -> Import CSV... -> Import EArray"))

        # Add actions to the Import submenu
        keys = ('import_table', 'import_array', 'import_carray', 
            'import_earray')
        vitables.utils.addActions(self.import_submenu, keys, actions)

        # Add submenu to file menu before the Close File action
        for item in self.vtgui.file_menu.actions():
            if item.objectName() == 'fileClose':
                self.vtgui.file_menu.insertMenu(item, self.import_submenu)
                self.vtgui.file_menu.insertSeparator(item)

        # Add submenu to file context menu before the Close File action
        cmenu = self.vtgui.view_cm
        for item in cmenu.actions():
            if item.objectName() == 'fileClose':
                cmenu.insertMenu(item, self.import_submenu)
                cmenu.insertSeparator(item)


    def createDestFile(self, filepath):
        """Create the PyTables file where the CSV file will be imported.

        :Parameter `filepath`: the PyTables file filepath
        """


        dbdoc = None
        try:
            dirname, filename = os.path.split(filepath)
            root = os.path.splitext(filename)[0]
            dest_filepath = os.path.join(dirname, '%s.h5' % root)
            if isValidFilepath(dest_filepath):
                dbdoc = self.dbt_model.createDBDoc(dest_filepath)
        except:
            print trs(
                """\nWarning: import failed """
                """because destination file cannot be created.""",
                'A file creation error')
            vitables.utils.formatExceptionInfo()

        return dbdoc


    def csvFilepath(self, leaf_kind):
        """Get the filepath of the source CSV file.

        :Parameter `leaf_kind`: the kind of container where data will be stored
        """

        # Call the file selector (and, if needed, customise it)
        filepath, working_dir = vitables.utils.getFilepath(\
            self.vtgui, 
            trs('Importing CSV file into %s',
                'Caption of the Import from CSV dialog') % leaf_kind, 
            dfilter=trs("""CSV Files (*.csv);;"""
                """All Files (*)""", 'Filter for the Import from CSV dialog'), 
            settings={'accept_mode': QtGui.QFileDialog.AcceptOpen, 
            'file_mode': QtGui.QFileDialog.ExistingFile, 
            'history': self.vtapp.file_selector_history, 
            'label': trs('Import', 'Accept button text for QFileDialog')}
            )

        if not filepath:
            # The user has canceled the dialog
            return

        # Update the history of the file selector widget
        self.vtapp.updateFSHistory(working_dir)

        return filepath


    def importTable(self):
        """Import a plain CSV file into a tables.Array object.

        :Parameter `kind`: the kind of array to be created (EArray, CArray)
        """

        kind = 'Table'
        filepath = self.csvFilepath(kind)
        if filepath is None:
            return

        # Import the CSV content
        try:
            QtGui.qApp.processEvents()
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            input_handler = open(filepath, 'r+')
            (nrows, descr, has_header) = tableInfo(input_handler)

            # Create the dataset
            dbdoc = self.createDestFile(filepath)
            if dbdoc is None:
                return
            io_filters = tables.Filters(complevel=9, complib='lzo')
            dataset_name = "imported_%s" % kind
            atitle = 'Source CSV file %s' % \
                os.path.basename(filepath)
            dataset = dbdoc.h5file.createTable('/', dataset_name, descr, 
                title=atitle, filters=io_filters, expectedrows=nrows)

            # Fill the dataset in a memory effcient way
            input_handler.seek(0)
            if has_header:
                # Skip the header line
                input_handler.readline()
            chunk_size = 10000
            buf_size = chunk_size*dataset.rowsize
            read_fh = input_handler.readlines
            buf = read_fh(buf_size)
            while buf:
                idata = getArray(buf)
                # Append data to the dataset
                dataset.append(idata)
                dataset.flush()
                del idata
                buf = read_fh(buf_size)
            dbdoc.h5file.flush()
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtGui.qApp.restoreOverrideCursor()
            input_handler.close()


    def importEArray(self):
        """Import a plain CSV file into a tables.EArray object.

        This is a slot method. See `addEntry` method for details.
        """

        kind = 'EArray'
        filepath = self.csvFilepath(kind)
        if filepath is None:
            return

        # Import the CSV content
        try:
            QtGui.qApp.processEvents()
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            chunk_size = 10000
            input_handler = open(filepath, 'r+')
            (nrows, atom, array_shape) = earrayInfo(input_handler)

            # Create the dataset
            dbdoc = self.createDestFile(filepath)
            if dbdoc is None:
                return
            io_filters = tables.Filters(complevel=9, complib='lzo')
            dataset_name = "imported_%s" % kind
            atitle = 'Source CSV file %s' % \
                os.path.basename(filepath)
            dataset = dbdoc.h5file.createEArray('/', dataset_name, atom, 
                array_shape, title=atitle, filters=io_filters, 
                expectedrows=nrows)

            # Fill the dataset in a memory effcient way
            input_handler.seek(0)
            chunk_size = 10000
            buf_size = chunk_size*dataset.rowsize
            read_fh = input_handler.readlines
            buf = read_fh(buf_size)
            while buf:
                idata = getArray(buf)
                # Append data to the dataset
                dataset.append(idata)
                dataset.flush()
                del idata
                buf = read_fh(buf_size)
            dbdoc.h5file.flush()
        except ValueError:
            print trs("""\nError: please, make sure that you are """\
                """importing a homogeneous dataset.""",
                'CSV file not imported error')
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtGui.qApp.restoreOverrideCursor()
            input_handler.close()


    def importCArray(self):
        """Import a plain CSV file into a tables.CArray object.

        This is a slot method. See `addEntry` method for details.
        """

        kind = 'CArray'
        filepath = self.csvFilepath(kind)
        if filepath is None:
            return

        # Import the CSV content
        try:
            QtGui.qApp.processEvents()
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            chunk_size = 10000
            input_handler = open(filepath, 'r+')
            (atom, array_shape) = carrayInfo(input_handler)

            # Create the dataset
            dbdoc = self.createDestFile(filepath)
            if dbdoc is None:
                return
            io_filters = tables.Filters(complevel=9, complib='lzo')
            dataset_name = "imported_%s" % kind
            atitle = 'Source CSV file %s' % \
                os.path.basename(filepath)
            dataset = dbdoc.h5file.createCArray('/', dataset_name, atom, 
                array_shape, title=atitle, filters=io_filters)

            # Fill the dataset in a memory effcient way
            input_handler.seek(0)
            chunk_size = 10000
            buf_size = chunk_size*dataset.rowsize
            read_fh = input_handler.readlines
            buf = read_fh(buf_size)
            start = 0
            while buf:
                idata = getArray(buf)
                stop = start + idata.shape[0]
                # Append data to the dataset
                dataset[start:stop] = idata
                dataset.flush()
                del idata
                start = stop
                buf = read_fh(buf_size)
            dbdoc.h5file.flush()
        except ValueError:
            print trs("""\nError: please, make sure that you are """\
                """importing a homogeneous dataset.""",
                'CSV file not imported error')
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtGui.qApp.restoreOverrideCursor()
            input_handler.close()


    def importArray(self):
        """Import a plain CSV file into a tables.Array object.

        This is a slot method. See `addEntry` method for details.
        """

        kind = 'Array'
        filepath = self.csvFilepath(kind)
        if filepath is None:
            return

        # Import the CSV content
        try:
            QtGui.qApp.processEvents()
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            # The dtypes are determined by the contents of each column
            # Multidimensional columns will have string datatype
            data = numpy.genfromtxt(filepath, delimiter=',', dtype=None)

            # Create the array
            dbdoc = self.createDestFile(filepath)
            if dbdoc is None:
                return
            array_name = "imported_%s" % kind
            title = 'Imported from CSV file %s' % \
                os.path.basename(filepath)
            dbdoc.h5file.createArray('/', array_name, data, title=title)
            dbdoc.h5file.flush()
        except TypeError:
            print trs("""\nError: please, make sure that you are """\
                """importing a homogeneous dataset.""",
                'CSV file not imported error')
            self.dbt_model.closeDBDoc(dbdoc.filepath)
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtGui.qApp.restoreOverrideCursor()
            del data


    def helpAbout(self):
        """Brief description of the plugin."""

        # Text to be displayed
        about_text = trs(
            """<qt>
            <p>Plugin that provides import CSV files capabilities.
            <p>CSV files can be imported into any of the following 
            PyTables containers: Array, EArray, CArray and Table.
            <p>When a file is imported into a Table automatic header
            detection is provided.
            <p>Beware that importing large files is a potentially slow 
            process because the whole file has to be read from disk, 
            transformed and write back to disk again so there is a lot 
            of disk IO.
            </qt>""",
            'Text of an About plugin message box')

        descr = dict(module_name='import_csv.py', 
            folder=os.path.join(PLUGINSDIR, 'csv'), 
            version=__version__, 
            plugin_name='Import from CSV', 
            author='Vicent Mas <vmas@vitables.org>', 
            descr=about_text)

        return descr
