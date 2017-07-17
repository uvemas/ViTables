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
# Plugin initial draft author: Jorge Ibanez jorge.ibannez@uam.es
#

"""Convenience functions for the import_csv.py module.
"""

__docformat__ = 'restructuredtext'

import logging
import os
import re
import tempfile
import traceback
import vitables.utils

import numpy
from qtpy import QtWidgets
import tables


translate = QtWidgets.QApplication.translate
TYPE_ERROR = translate(
    'ImportCSV', 'Please, make sure that you are importing a '
    'homogeneous dataset.', 'CSV file not imported error')

log = logging.getLogger(__name__)


def getArray(buf):
    """Fill an intermediate ``numpy`` array with data read from the `CSV` file.

    The lines read from the CSV file are stored in a temporary file which is
    passed to numpy.genfromtxt() in order to create a numpy array.

    The dtypes of the numpy array are determined by the contents of each column.
    Multidimensional columns will have string datatype.

    Warning: the temporary file is written in binary mode so lines are stored
    as bytearrays (encoded as UTF-8). It means that strings in the numpy array
    will also be bytes with UTF-8 encoding and not Python 3 strings.

    :Parameter buf: the data buffer is a list of lines of the CSV file
    """

    with tempfile.TemporaryFile(mode='w+b') as temp_file:
        for line in buf:
            temp_file.write(bytearray(line, 'UTF-8'))
        temp_file.seek(0)
        data = numpy.genfromtxt(temp_file, delimiter=',', dtype=None)
    return data


def tableInfo(input_handler):
    """Return useful information about the `tables.Table` being created.

    :Parameter input_handler: the file handler of the inspected CSV file
    """

    # Inspect the CSV file reading its second line
    # (reading the first line is not safe as it could be a header)
    input_handler.seek(0)
    first_line = getArray(input_handler.readline())
    try:
        second_line = getArray(input_handler.readline())
    except IOError:
        # The second line cannot be read. We assume there is only on line
        second_line = first_line

    # Estimate the number of rows of the CSV file
    filesize = os.path.getsize(input_handler.name)
    # Record size = number of elements * element size
    record_size = second_line.size * second_line.itemsize
    nrows = filesize / record_size

    if second_line.dtype.fields is None:
        # second_line is a homogeneous array
        descr, has_header = \
            homogeneousTableInfo(input_handler, first_line, second_line)
    else:
        # second_line is a heterogeneous array
        descr, has_header = \
            heterogeneousTableInfo(input_handler, first_line, second_line)

    del second_line
    return (nrows, descr, has_header)


def heterogeneousTableInfo(input_handler, first_line, second_line):
    """Return useful information about the `tables.Table` being created.

    The `data` array is heterogenous, i.e. not all fields have the same
    dtype.

    :Parameters:

    - `input_handler`: the file handler of the inspected `CSV` file
    - `first_line`: a ``numpy`` array which contains the first line of the `CSV`
      file
    - `second_line`: a ``numpy`` array which contains the second line of the
      `CSV` file
    """

    has_header = False
    fl_dtype = first_line.dtype
    if (fl_dtype.fields is None) and (fl_dtype.char in('S', 'U')):
        has_header = True

    # Stuff used for finding out itemsizes of string fields
    itemsizes = {}
    for field in range(0, len(second_line.dtype)):
        if second_line.dtype[field].name.startswith('str') or \
                second_line.dtype[field].name.startswith('bytes'):
            itemsizes[field] = 0

    # If a dtype is a string, find out its biggest itemsize
    if itemsizes:
        buf_size = 1024 * 1024
        input_handler.seek(0)
        if has_header:
            # Skip the header
            input_handler.readline()
        buf = input_handler.readlines(buf_size)
        while buf:
            temp_file = tempfile.TemporaryFile()
            for line in buf:
                temp_file.write(bytearray(line, 'UTF-8'))
            for field in itemsizes.keys():
                temp_file.seek(0)
                idata = numpy.genfromtxt(temp_file, delimiter=',',
                                         usecols=(field,), dtype=None)
                itemsizes[field] = max(itemsizes[field], idata.dtype.itemsize)
                del idata
            temp_file.close()
            buf = input_handler.readlines(buf_size)

    if has_header:
        descr = {}
        for i in range(0, first_line.size):
            dtype = second_line.dtype.fields['f{0}'.format(i)][0]
            descr[first_line[i].decode('UTF-8')] = tables.Col.from_dtype(dtype,
                                                                         pos=i)
        for i in itemsizes:
            descr[first_line[i].decode(
                'UTF-8')] = tables.StringCol(itemsizes[i], pos=i)
    else:
        descr = dict([(f, tables.Col.from_dtype(t[0])) for f, t in
                      second_line.dtype.fields.items()])
        for i in itemsizes:
            descr['f{0}'.format(i)] = tables.StringCol(itemsizes[i])

    return descr, has_header


def homogeneousTableInfo(input_handler, first_line, second_line):
    """Return useful information about the `tables.Table` being created.

    The `second_line` array is homegenous, i.e. all fields have the same dtype.

    :Parameters:

    - `input_handler`: the file handler of the inspected `CSV` file
    - `first_line`: a ``numpy`` array which contains the first line of the
      `CSV` file
    - `second_line`: a ``numpy`` array which contains the second line of the 
      `CSV` file
    """

    # Find out if the table has a header or not.
    has_header = False
    fldn = first_line.dtype.name
    sldn = second_line.dtype.name
    if sldn.startswith('str') or sldn.startswith('bytes'):
        answer = askForHelp(first_line)
        if answer == 'Header':
            has_header = True
    elif fldn.startswith('str') or fldn.startswith('bytes'):
        has_header = True

    input_handler.seek(0)
    if has_header:
        # Skip the header
        input_handler.readline()

    # If the fields of the table are strings then find out the biggest itemsize
    if sldn.startswith('str') or sldn.startswith('bytes'):
        itemsize = 0
        buf_size = 1024 * 1024
        buf = input_handler.readlines(buf_size)
        if not buf:
            # If the CSV file contains just one line
            itemsize = first_line.dtype.itemsize
        while buf:
            idata = getArray(buf)
            itemsize = max(itemsize, idata.dtype.itemsize)
            del idata
            buf = input_handler.readlines(buf_size)

    # Iterate over the data fields and make the table description
    # If the CSV file contains just one field then first_line is a
    # scalar array and cannot be iterated so we reshape it
    if first_line.shape == ():
        first_line = first_line.reshape(1,)
    indices = list(range(0, first_line.shape[0]))

    if has_header:
        if sldn.startswith('str') or sldn.startswith('bytes'):
            descr = dict([(first_line[i].decode('UTF-8'),
                           tables.StringCol(itemsize, pos=i))
                          for i in indices])
        else:
            descr = dict([(first_line[i].decode('UTF-8'),
                           tables.Col.from_dtype(second_line.dtype, pos=i))
                          for i in indices])
    else:
        if sldn.startswith('str') or sldn.startswith('bytes'):
            descr = dict([('f{0}'.format(field), tables.StringCol(itemsize))
                          for field in indices])
        else:
            descr = dict([('f{0}'.format(field),
                           tables.Col.from_dtype(second_line.dtype))
                          for field in indices])

    return descr, has_header


def askForHelp(first_line):
    """Ask user if the first row is a header.

    :Parameter first_line: a ``numpy`` array which contains the first line of
      the `CSV` file
    """

    title = translate('ImportCSV', 'Resolving first line role',
                      'Message box title')
    text = translate('ImportCSV', 'Does the first line of the file contain '
                     'a table header or regular data?', 'Message box text')
    itext = ''
    try:
        from functools import reduce
        dtext = reduce(lambda x, y: '{0}, {1}'.format(x, y), first_line)
    except TypeError:
        # If first_line has only one field reduce raises a TypeError
        dtext = first_line.tostring()
    buttons = {
        'Header':
        (translate('ImportCSV', 'Header', 'Button text'),
         QtWidgets.QMessageBox.YesRole),
        'Data':
        (translate('ImportCSV', 'Data', 'Button text'),
         QtWidgets.QMessageBox.NoRole),
    }
    return vitables.utils.questionBox(title, text, itext, dtext, buttons)


def earrayInfo(input_handler):
    """Return useful information about the `tables.EArray` being created.

    :Parameter input_handler: the file handler of the inspected file
    """

    # Inspect the CSV file reading its first line
    # The dtypes are determined by the contents of each column
    # Multidimensional columns will have string datatype
    first_line = getArray(input_handler.readline())

    # Estimate the number of rows of the file
    filesize = os.path.getsize(input_handler.name)
    record_size = first_line.size * first_line.itemsize
    nrows = filesize / record_size

    if first_line.dtype.name.startswith('str') or \
            first_line.dtype.name.startswith('bytes'):
        # Find out the biggest itemsize
        itemsize = 0
        buf_size = 1024 * 1024
        input_handler.seek(0)
        buf = input_handler.readlines(buf_size)
        while buf:
            idata = getArray(buf)
            itemsize = max(itemsize, idata.dtype.itemsize)
            del idata
            buf = input_handler.readlines(buf_size)
        atom = tables.StringAtom(itemsize)
    else:
        # With compound dtypes this will raise a ValueError
        atom = tables.Atom.from_dtype(first_line.dtype)

    # Get the data shape
    if nrows < 2:
        # Corner case: the file only has one row
        array_shape = (0, )
    elif first_line.shape == ():
        # Corner case: the file has just one column
        array_shape = (0, )
    else:
        # General case: the file is a MxN array
        array_shape = (0, first_line.shape[0])

    del first_line
    input_handler.seek(0)
    return nrows, atom, array_shape


def carrayInfo(input_handler):
    """Return useful information about the `tables.CArray` being created.

    :Parameter input_handler: the file handler of the inspected file
    """

    # Inspect the CSV file reading its first line
    # The dtypes are determined by the contents of each column
    # Multidimensional columns will have string datatype
    input_handler.seek(0)
    first_line = getArray(input_handler.readline())

    # This counting algorithm is faster than looping over lines with
    # fh.readline and incrementing a counter at every step
    lines = 0
    itemsize = 0
    buf_size = 1024 * 1024
    input_handler.seek(0)

    if first_line.dtype.name.startswith('str') or \
            first_line.dtype.name.startswith('bytes'):
        # Count lines and find out the biggest itemsize
        buf = input_handler.readlines(buf_size)
        while buf:
            idata = getArray(buf)
            itemsize = max(itemsize, idata.dtype.itemsize)
            del idata
            lines += len(buf)
            buf = input_handler.readlines(buf_size)
    else:
        # Count lines
        buf = input_handler.readlines(buf_size)
        while buf:
            lines += len(buf)
            buf = input_handler.readlines(buf_size)

    if itemsize:
        atom = tables.StringAtom(itemsize)
    else:
        atom = tables.Atom.from_dtype(first_line.dtype)

    # Get the data shape
    if lines == 1:
        # Corner case: the file only has one row
        array_shape = first_line.shape
        lines = first_line.shape[0]
    elif first_line.shape == ():
        # Corner case: the file has just one column
        array_shape = (lines, )
    else:
        # General case: the file is a MxN array
        array_shape = (lines, first_line.shape[0])

    del first_line
    input_handler.seek(0)
    return atom, array_shape


def isValidFilepath(filepath):
    """Check the filepath of the destination file.

    :Parameter filepath: the filepath where the imported dataset will live
    """
    valid = True
    if os.path.exists(filepath):
        log.error(translate(
            'ImportCSV',
            'CSV import failed because destination file already exists.',
            'A file creation error'))
        valid = False

    elif os.path.isdir(filepath):
        log.error(translate(
            'ImportCSV',
            'CSV import failed because destination container is a directory.',
            'A file creation error'))
        valid = False

    return valid


def checkFilenameExtension(filepath):
    """
    Check the filename extension of the CSV file.

    If the filename has no extension this method adds .csv
    extension to it.

    :Parameter filepath: the full path of the file

    :Returns: the filepath with the proper extension
    """

    if not re.search(r'\.(.+)$', os.path.basename(filepath)):
        ext = '.csv'
        filepath = filepath + ext
    return filepath
