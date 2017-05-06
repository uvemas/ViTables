#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
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

"""
When a user edits the attributes of a node using the Properties dialog and
presses `OK` the attributes correctness is checked by this module. Datatypes
and overflow conditions are checked. If no errors are detected the new set of
attributes is stored in the `PyTables` node. Otherwise the user is reported
about the error and the dialog remains open so the user can fix her mistake.
"""

__docformat__ = 'restructuredtext'

import tables
import numpy

from qtpy import QtGui
from qtpy import QtWidgets

import vitables.utils

translate = QtWidgets.QApplication.translate


def checkSyntax(value):
    """Check the syntax of a `Python` expression.

    :Parameters value: the Python expression to be evaluated
    """

    if value[0] in ("'", '"'):
        # Quotes are not permitted in the first position
        return False
    try:
        eval(value)
    except (ValueError, SyntaxError):
        return False
    else:
        return True


def formatStrValue(dtype, str_value):
    """
    Format the string representation of a value accordingly to its datatype.

    This function catches datatype errors for boolean values.

    :Parameters:

    - dtype: the value data type
    - str_value: the string representation of a value
    """

    if dtype == 'bool':
        # Every listed value is valid but none of them would
        # pass the out of range test later so we use a fake
        # valid value.
        # Beware that numpy.array(True).astype('bool')[()] fails
        # with a TypeError so we use '1' as a fake value
        if str_value in ['1', 'TRUE', 'True', 'true']:
            str_value = '1'
        elif str_value in ['0', 'FALSE', 'False', 'false']:
            str_value = '0'
        else:
            raise ValueError
    elif dtype.startswith('complex'):
        # Valid complex literal strings do not have parenthesis
        if str_value.startswith('(') and str_value.endswith(')'):
            str_value = str_value[1:-1]

    return str_value


def checkValue(dtype, str_value):
    """
    Check for overflow errors and dtype errors on integer and float values.

    By default, when overflow occurs in the creation of a ``numpy`` array,
    it is silently converted to the desired datatype:

    >>> numpy.array(-4).astype(numpy.uint8)
    array(252, dtype=uint8)
    >>> numpy.array(1420).astype(numpy.int8)
    array(-116, dtype=int8)

    This behavior can be acceptable for a library, but not for an end
    user application as ``ViTables`` so we have to catch such cases.

    :Parameters:

    - dtype: the value datatype
    - str_value: the string representation of a value
    """

    dtypes_map = {
        'int8': numpy.int8, 'int16': numpy.int16,
        'int32': numpy.int32, 'int64': numpy.int64,
        'uint8': numpy.uint8, 'uint16': numpy.uint16,
        'uint32': numpy.uint32, 'uint64': numpy.uint64,
        'float32': numpy.float32, 'float64': numpy.float64,
        }

    # For Python objects and strings no overflow can occur
    if dtype not in dtypes_map:
        return str_value

    new_array = numpy.array(str_value).astype(dtype)
    # Catches unexpected results from conversions
    # Examples: numpy.array('-23').astype('unint8') -> mismatch dtype
    # or numpy.array('99999').astype('int8') -> overflow
    if str(new_array[()]) != str_value:
        raise RuntimeWarning
    # If no errors are found return the original value
    return str_value


class AttrEditor(object):
    """
    Setup the attributes entered in the Properties dialog.

    When the user edits the Attributes Set Instance (see `PyTables` manual
    for details) of a given node via the Properties dialog and presses `OK`
    the validity of the new set of attributes is checked. If it is fine
    then the old `ASI` is replaced by the new one and the dialog is closed.
    If an error is found in the new set of attributes then the dialog
    remains opened until the user fixes the mistake.

    :Parameters:

    - `asi`: the Attributes Set Instance being updated
    - `title`: the TITLE attribute entered by the user in the Properties dialog
    - `user_table`: the table of user attributes edited by the user in the
        Properties dialog
    """

    def __init__(self, asi, title, user_table):
        """Initialise the attributes checker."""

        self.asi = asi

        # A dictionary with the attributes that have to be checked
        self.edited_attrs = {}
        model = user_table.model()
        rows = model.rowCount()
        # Parse the table and get string representations of its cell contents
        for row in range(0, rows):
            # As ViTables doesn't support editing ND-array attributes they
            # are marked in order to be found later
            name_item = model.item(row, 0)
            if not name_item.isEditable():
                multidim = True
            else:
                multidim = False
            name = model.item(row, 0).text()
            value = model.item(row, 1).text()
            dtype_index = model.indexFromItem(model.item(row, 2))
            dtype = user_table.indexWidget(dtype_index).currentText()
            self.edited_attrs[row] = (name, value, dtype, multidim)

        # Add the TITLE attribute to the dictionary
        if title is not None:
            self.edited_attrs[rows] = ('TITLE', title, 'string', False)


    def checkAttributes(self):
        """
        Check the user attributes table.

        If empty or repeated names, values mismatching the
        attribute type or out of range values are found then an error is
        reported. If the table is OK the node `ASI` is updated and the
        Properties dialog is closed.

        The attributes checked here are those of self.edited_attrs dict so the
        values are all string
        """

        # Error message for mismatching value/type pairs
        dtype_error = translate('AttrEditor', """\nError: "{0}" value """
            """mismatches its data type.""",
            'User attributes table editing error')

        # Error message for overflow values
        range_error = translate('AttrEditor', """\nError: "{0}" value """
            """is out of range.""",
            'User attributes table editing error')

        # Some times it's difficult to find out if the error
        # is due to a mismatch or to an overflow
        conversion_error = translate('AttrEditor', """\nError: "{0}" value """
            """is out of range or mismatches its data type.""",
            'User attributes table editing error')

        # Error message for syntax errors in Python attributes
        syntax_error = translate('AttrEditor', """\nError: "{0}" """
            """cannot be converted to a Python object.""",
            'User attributes table editing error')

        rows_range = self.edited_attrs.keys()

        # Check for empty Name cells
        for row in rows_range:
            name = self.edited_attrs[row][0]
            # Empty Value cells are acceptable for string attributes
            # but empty Name cells are invalid
            if name == '':
                return (False,
                        translate('AttrEditor',
                            "\nError: empty field Name in the row {0:d}",
                            'User attrs editing error').format(int(row + 1)))

        # Check for repeated names
        names_list = []
        for row in rows_range:
            name = self.edited_attrs[row][0]
            if not name in names_list:
                names_list.append(name)
            else:
                return (False,
                        translate('AttrEditor',
                            '\nError: attribute name "{0}" is repeated.',
                            'User attrs table editing error').format(name))

        # Check for dtype, range and syntax correctness of scalar attributes
        for row in rows_range:
            name, value, dtype, multidim = self.edited_attrs[row]
            if multidim == True:
                continue
            if dtype == 'python':
                # Check the syntax of the Python expression
                if not checkSyntax(value):
                    return (False, syntax_error.format(name))
            elif dtype == 'string':
                dtype = 'str'
            elif dtype == 'bytes':
                pass
            else:
                # Format properly the string representation of value
                # and check for dtype and overflow errors
                try:
                    value = formatStrValue(dtype, value)
                    value = checkValue(dtype, value)
                except OverflowError:
                    return (False, range_error.format(name))
                except ValueError:
                    return (False, dtype_error.format(name))
                except RuntimeWarning:
                    return (False, conversion_error.format(name))

            # If the attribute passes every test then its entry in the
            # dictionary of edited attributes is updated
            self.edited_attrs[row] = name, value, dtype, multidim

        return (True, None)


    def setAttributes(self):
        """
        Update edited attributes.

        This method is called when the user has successfully edited some
        attribute in the Properties dialog. If it happens then this method
        updates the `ASI` of the inspected `PyTables` node.
        """

        # Get rid of deleted attributes
        if 'TITLE' in self.edited_attrs:
            all_attrs = frozenset(self.asi._v_attrnamesuser + ["TITLE"])
        else:
            all_attrs = frozenset(self.asi._v_attrnamesuser)
        edited_attrs_names = frozenset([self.edited_attrs[row][0]
                                        for row in self.edited_attrs.keys()])
        for attr in (all_attrs - edited_attrs_names):
            try:
                self.asi._v_node._f_delattr(attr)
            except (tables.NodeError, AttributeError):
                vitables.utils.formatExceptionInfo()

        for row in self.edited_attrs.keys():
            # Scalar attributes are stored as
            # numpy scalar arrays of the proper type
            name, value, dtype, multidim = self.edited_attrs[row]
            if multidim == True:
                continue

            if dtype == 'python':
                value = eval('{0}'.format(value))
            elif dtype == 'bytes':
                # Remove the prefix and enclosing quotes
                value = value[2:-1]
                value = numpy.array(value).astype(dtype)[()]
            else:
                value = numpy.array(value).astype(dtype)[()]

            # Updates the ASI
            try:
                setattr(self.asi, name, value)
            except AttributeError:
                vitables.utils.formatExceptionInfo()
