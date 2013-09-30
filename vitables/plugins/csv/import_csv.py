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

#
# Plugin initial draft author: Jorge Ibanez jorge.ibannez@uam.es
#

"""Plugin that provides import `CSV` files into `PyTables` arrays and tables.

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

__docformat__ = 'restructuredtext'
__version__ = '1.0'
plugin_class = 'ImportCSV'
plugin_name = 'CSV importer'
comment = 'Import CSV files into datasets.'

import os
import tempfile

import tables
import numpy

from PyQt4 import QtCore
from PyQt4 import QtGui


import vitables.utils
import vitables.plugin_utils
from vitables.vtsite import PLUGINSDIR
from vitables.plugins.csv.aboutpage import AboutPage

translate = QtGui.QApplication.translate
TYPE_ERROR = translate('ImportCSV', 
            """\nError: please, make sure that you are importing a """
            """homogeneous dataset.""", 'CSV file not imported error')

def getArray(buf):
    """Fill an intermediate ``numpy`` array with data read from the `CSV` file.

    The dtypes are determined by the contents of each column.
    Multidimensional columns will have string datatype.

    :Parameter buf: the data buffer
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
    """Return useful information about the `tables.Table` being created.

    :Parameter input_handler: the file handler of the inspected file    
    """

    # Inspect the CSV file reading its second line
    # (reading the first line is not safe enough as it could be a header)
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
    """Return useful information about the `tables.Table` being created.

    The `data` array is heterogenous, i.e. not all fields have the same
    dtype.

    :Parameters:

    - `input_handler`: the file handler of the inspected `CSV` file
    - `first_line`: a numpy array which contains the first line of the `CSV` 
      file
    - `data`: a numpy array which contains the second line of the `CSV` file
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
            dtype = data.dtype.fields['f{0}'.format(i)][0]
            descr[first_line[i]] = tables.Col.from_dtype(dtype, pos=i)
        for i in itemsizes:
            descr[first_line[i]] = tables.StringCol(itemsizes[i], pos=i)
    else:
        descr = dict([(f, tables.Col.from_dtype(t[0])) for f, t in 
            data.dtype.fields.items()])
        for i in itemsizes:
            descr['f{0}'.format(i)] = tables.StringCol(itemsizes[i])

    return descr, has_header


def homogeneousTableInfo(input_handler, first_line, data):
    """Return useful information about the `tables.Table` being created.

    The `data` array is homegenous, i.e. all fields have the same dtype.

    :Parameters:

    - `input_handler`: the file handler of the inspected `CSV` file
    - `first_line`: a ``numpy`` array which contains the first line of the 
      `CSV` file
    - `data`: a numpy array which contains the second line of the `CSV` file
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
            descr = dict(
                [('f{0}'.format(field), tables.StringCol(itemsize)) \
                for field in indices])
        else:
            descr = dict(
                [('f{0}'.format(field), tables.Col.from_dtype(data.dtype)) \
                for field in indices])

    return descr, has_header


def askForHelp(first_line):
    """Ask to user if the first row is a header.

    :Parameter first_line: a numpy array which contains the first line of 
      the `CSV` file
    """

    title = translate('ImportCSV', 'Resolving first line role', 
        'Message box title')
    text = translate('ImportCSV', """Does the first line of the file contain"""
        """ a table header or regular data?""", 'Message box text')
    itext = ''
    try:
        dtext = reduce(lambda x, y: u'{0}, {1}'.format(x, y), first_line)
    except TypeError:
        # If first_line has only one field reduce raises a TypeError
        dtext = first_line.tostring()
    buttons = {
        'Header': 
            (translate('ImportCSV', 'Header', 'Button text'), 
            QtGui.QMessageBox.YesRole), 
        'Data': 
            (translate('ImportCSV', 'Data', 'Button text'), 
            QtGui.QMessageBox.NoRole),
        }
    return vitables.utils.questionBox(title, text, itext, dtext, buttons)


def earrayInfo(input_handler):
    """Return useful information about the `tables.EArray` being created.

    :Parameter input_handler: the file handler of the inspected file
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
    """Return useful information about the `tables.CArray` being created.

    :Parameter input_handler: the file handler of the inspected file
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

    :Parameter filepath: the filepath where the imported dataset will live
    """


    valid = True
    if os.path.exists(filepath):
        print(translate('ImportCSV', 
            """\nWarning: """
            """import failed because destination file already exists.""",
            'A file creation error'))
        valid = False

    elif os.path.isdir(filepath):
        print(translate('ImportCSV', 
            """\nWarning: import failed """
            """because destination container is a directory.""",
            'A file creation error'))
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

        super(ImportCSV, self).__init__()

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()
        if self.vtapp is None:
            return

        self.vtgui = vitables.plugin_utils.getVTGui()
        self.dbt_model = self.vtgui.dbs_tree_model
        self.dbt_view = self.vtgui.dbs_tree_view

        # Add an entry under the File menu
        self.addEntry()


    def addEntry(self):
        """Add the `Import CSV...` entry to the `File` menu.
        """

        icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(PLUGINSDIR, \
            'csv/icons/document-import.png'))
        icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)

        self.import_submenu = \
            QtGui.QMenu(translate('ImportCSV', 
                'I&mport from CSV...','File -> Import CSV'))
        self.import_submenu.setSeparatorsCollapsible(False)
        self.import_submenu.setIcon(icon)

        # Create the actions
        actions = {}
        actions['import_table'] = QtGui.QAction(
            translate('ImportCSV', "Import &Table...", 
                "Import table from CSV file"), 
            self, 
            shortcut=QtGui.QKeySequence.UnknownKey, 
            triggered=self.csv2Table, 
            statusTip=translate('ImportCSV', 
                "Import Table from plain CSV file", 
                "Status bar text for File -> Import CSV... -> Import Table"))

        actions['import_array'] = QtGui.QAction(
            translate('ImportCSV', "Import &Array...", 
                "Import array from CSV file"), 
            self, 
            shortcut=QtGui.QKeySequence.UnknownKey, 
            triggered=self.csv2Array, 
            statusTip=translate('ImportCSV', 
                "Import Array from plain CSV file", 
                "Status bar text for File -> Import CSV... -> Import Array"))

        actions['import_carray'] = QtGui.QAction(
            translate('ImportCSV', "Import &CArray...", 
                "Import carray from CSV file"), 
            self, 
            shortcut=QtGui.QKeySequence.UnknownKey, 
            triggered=self.csv2CArray, 
            statusTip=translate('ImportCSV', 
                "Import CArray from plain CSV file",
                "Status bar text for File -> Import CSV... -> Import CArray"))

        actions['import_earray'] = QtGui.QAction(
            translate('ImportCSV', "Import &EArray...", 
                "Import earray from CSV file"), 
            self, 
            shortcut=QtGui.QKeySequence.UnknownKey, 
            triggered=self.csv2EArray,
            statusTip=translate('ImportCSV', 
                "Import EArray from plain CSV file", 
                "Status bar text for File -> Import CSV... -> Import EArray"))

        actions['separator'] = QtGui.QAction(self)
        actions['separator'].setSeparator(True)

        # Add actions to the Import submenu
        keys = ('import_table', 'import_array', 'import_carray', 
            'import_earray')
        vitables.utils.addActions(self.import_submenu, keys, actions)

        # Add submenu to file menu before the Close File action
        vitables.plugin_utils.insertInMenu(self.vtgui.file_menu,
            self.import_submenu, 'fileClose')
        sep = actions['separator']
        vitables.plugin_utils.insertInMenu(self.vtgui.file_menu, sep,
            'fileClose')

        # Add submenu to file context menu before the Close File action
        vitables.plugin_utils.insertInMenu(self.vtgui.view_cm,
            self.import_submenu, 'fileClose')
        vitables.plugin_utils.insertInMenu(self.vtgui.view_cm, sep,
            'fileClose')


    def createDestFile(self, filepath):
        """Create the `PyTables` file where the `CSV` file will be imported.

        :Parameter filepath: the `PyTables` file filepath
        """


        dbdoc = None
        try:
            dirname, filename = os.path.split(filepath)
            root = os.path.splitext(filename)[0]
            dest_filepath = os.path.join(dirname, u'{0}.h5'.format(root))
            if isValidFilepath(dest_filepath):
                dbdoc = self.dbt_model.createDBDoc(dest_filepath)
        except:
            print(translate('ImportCSV', 
                """\nWarning: import failed """
                """because destination file cannot be created.""",
                'A file creation error'))
            vitables.utils.formatExceptionInfo()

        return dbdoc


    def csvFilepath(self, leaf_kind):
        """Get the filepath of the source `CSV` file.

        :Parameter leaf_kind: the kind of container where data will be stored
        """

        # Call the file selector (and, if needed, customise it)
        filepath, working_dir = vitables.utils.getFilepath(\
            self.vtgui, 
            translate('ImportCSV', 'Importing CSV file into {0}',
                'Caption of the Import from CSV dialog').format(leaf_kind), 
            dfilter=translate('ImportCSV', """CSV Files (*.csv);;"""
                """All Files (*)""", 'Filter for the Import from CSV dialog'), 
            settings={'accept_mode': QtGui.QFileDialog.AcceptOpen, 
            'file_mode': QtGui.QFileDialog.ExistingFile, 
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
            QtGui.qApp.processEvents()
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            input_handler = open(filepath, 'r+')
            (nrows, descr, has_header) = tableInfo(input_handler)

            # Create the dataset
            dbdoc = self.createDestFile(filepath)
            if dbdoc is None:
                return
            io_filters = tables.Filters(complevel=9, complib='lzo')
            dataset_name = u"imported_{0}".format(kind)
            atitle = \
                u'Source CSV file {0}'.format(os.path.basename(filepath))
            dataset = dbdoc.h5file.createTable('/', dataset_name, descr, 
                title=atitle, filters=io_filters, expectedrows=nrows)

            # Fill the dataset in a memory efficient way
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
            self.updateTree(dbdoc.filepath)
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtGui.qApp.restoreOverrideCursor()
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
            dataset_name = u"imported_{0}".format(kind)
            atitle = \
                u'Source CSV file {0}'.format(os.path.basename(filepath))
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
            self.updateTree(dbdoc.filepath)
        except ValueError:
            print(TYPE_ERROR)
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtGui.qApp.restoreOverrideCursor()
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
            dataset_name = u"imported_{0}".format(kind)
            atitle = \
                u'Source CSV file {0}'.format(os.path.basename(filepath))
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
            self.updateTree(dbdoc.filepath)
        except ValueError:
            print(TYPE_ERROR)
        except:
            vitables.utils.formatExceptionInfo()
        finally:
            QtGui.qApp.restoreOverrideCursor()
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
            QtGui.qApp.processEvents()
            QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
            # The dtypes are determined by the contents of each column
            # Multidimensional columns will have string datatype
            data = numpy.genfromtxt(filepath, delimiter=',', dtype=None)
        except TypeError:
            data = None
            dbdoc = None
            print(TYPE_ERROR)
        else:
            try:
                # Create the array
                dbdoc = self.createDestFile(filepath)
                if dbdoc is None:
                    return
                array_name = u"imported_{0}".format(kind)
                title = u'Imported from CSV file {0}'.\
                    format(os.path.basename(filepath))
                dbdoc.h5file.createArray('/', array_name, data, title=title)
                dbdoc.h5file.flush()
                self.updateTree(dbdoc.filepath)
            except TypeError:
                print(TYPE_ERROR)
            except:
                vitables.utils.formatExceptionInfo()
        finally:
            del data
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
            'about_text': translate('ImportCSV', 
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
            'Text of an About plugin message box')}
        about_page = AboutPage(desc, parent)
        return about_page
