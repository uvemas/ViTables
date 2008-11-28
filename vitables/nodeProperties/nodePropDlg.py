# -*- coding: utf-8 -*-

########################################################################
#
#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008 Vicent Mas. All rights reserved
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
#       $Source$
#       $Id: nodePropDlg.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the NodePropDlg class.

Classes:

* NodePropDlg(qt.QTabDialog)

Methods:

* __init__(self, info, mode='r')
* __tr(self, source, comment=None)
* slotCheckAttributes(self)
* updateTitle(self)
* checkUserAttributes(self)
* updateUserAttributes(self, nd_attrs)
* accept(self)

Functions:

* checkSyntax(value)
* formatStrValue(dtype, str_value)
* checkOverflow(dtype, str_value)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import sets

import numpy

import qt

import vitables.nodeProperties.leafProp as leafProp
import vitables.nodeProperties.groupProp as groupProp
import vitables.nodeProperties.systemAttr as systemAttr
import vitables.nodeProperties.userAttr as userAttr
import vitables.utils

def checkSyntax(value):
    """Check the syntax of a `Python` expression.

    :Parameters value: the Python expression to be evaluated
"""

    try:
        if (value[0], value[-1]) in [("'", "'"), ('"', '"')]:
            value = eval('\"%s\"' % value)
        else:
            value = eval('%s' % value)
    except:
        return False
    else:
        return True


def formatStrValue(dtype, str_value):
    """
    Format the string representation of a value accordingly to its data type.
    
    :Parameters:

    - dtype: the value data type
    - str_value: the string representation of a value
    """

    try:
        if dtype == 'bool':
            # Every listed value is valid but any of them would
            # pass the out of range test later so we use a fake
            # valid value.
            # Beware that numpy.array(True).astype('bool')[()] fails
            # with a TypeError so we use '1' as a fake value
            if str_value in ['1', 'TRUE', 'True', 'true']:
                str_value = '1'
            elif str_value in ['0', 'FALSE', 'False', 'false']:
                str_value = '0'
            else:
                raise TypeError
        elif dtype.startswith('complex'):
            # Valid complex literal strings do not have parenthesis
            if str_value.startswith('(') and str_value.endswith(')'):
                str_value = str_value[1:-1]
    except TypeError:
        return None
    else:
        return str_value


def checkOverflow(dtype, str_value):
    """
    Check for overflows in integer and float values.

    By default, when overflow occurs in the creation of a numpy array,
    it is silently converted to the desired data type:

    >>> numpy.array(-4).astype(numpy.uint8)
    array(252, dtype=uint8)
    >>> numpy.array(1420).astype(numpy.int8)
    array(-116, dtype=int8)

    This behavior can be acceptable for a library, but not for an end
    user application as ViTables so we have to catch such cases.

    :Parameters:

    - dtype: the value data type
    - str_value: the string representation of a value
    """

    dtypes_map = {
        'int8': numpy.int8, 'int16': numpy.int16,
        'int32': numpy.int32, 'int64': numpy.int64,
        'uint8': numpy.uint8, 'uint16': numpy.uint16,
        'uint32': numpy.uint32, 'uint64': numpy.uint64,
        'float32': numpy.float32, 'float64': numpy.float64,
        }

    if dtype not in dtypes_map:
        return str_value

    if dtype.startswith('float'):
        max = numpy.finfo(dtypes_map[dtype]).max
        min = numpy.finfo(dtypes_map[dtype]).min
        value = float(str_value)
    else:
        max = numpy.iinfo(dtypes_map[dtype]).max
        min = numpy.iinfo(dtypes_map[dtype]).min
        value = long(str_value)

    if value < min or value > max:
        raise ValueError
        return None
    else:
        return str_value


class NodePropDlg(qt.QTabDialog):
    """
    Node properties dialog.

    This class displays a tabbed dialog that shows some properties of the
    selected node. First tab, General, shows general properties like name,
    path, type etc. The second and third tabs show the system and user
    attributes in a tabular way.
    """


    def __init__(self, info, mode='r'):
        """:Parameters:

        - `info`: a dictionary containing the information to be displayed
        - `mode`: the access mode of the database to which the inspected node
            belongs. Can be 'r'ead-only or 'a'ppend.
        """

        qt.QTabDialog.__init__(self, qt.qApp.mainWidget())

        self.mode = mode

        self.attrs_are_ok = True

        # Boldface the dialog font
        font = self.font()
        font.setBold(1)
        self.setFont(font)

        # The caption
        node_type = info['type']
        if node_type.count('file'):
            self.setCaption(self.__tr('File properties',
                'Caption of the dialog'))
        elif node_type == 'Group':
            self.setCaption(self.__tr('Group properties',
                'Caption of the dialog'))
        elif node_type.count('Array'):
            self.setCaption(self.__tr('Array properties',
                'Caption of the dialog'))
        elif node_type == 'Table':
            self.setCaption(self.__tr('Table properties',
                'Caption of the dialog'))

        #
        # The General page ####################################################
        #

        # Makes the page
        if node_type.count('file'):
            self.general_page = groupProp.GroupGeneralPage(info, root=True)
        elif node_type == 'Group':
            self.general_page = groupProp.GroupGeneralPage(info)
        else:
            self.general_page = leafProp.LeafGeneralPage(info)

        # Adds page to dialog
        self.addTab(self.general_page, self.__tr('&General',
            'Title of the first dialog tab'))

        #
        # The Attributes pages ################################################
        #
        self.asi = info['asi']

        # Makes the system attributes page
        self.sys_attr_page = systemAttr.SysAttrPage(info['sysAttr'], self.mode)

        # Adds System page to dialog
        self.addTab(self.sys_attr_page, self.__tr('&System Attributes',
            'Title of the second dialog tab'))

        # Makes the user attributes page
        self.user_attr_page = userAttr.UserAttrPage(info['userAttr'], self.mode)

        # Adds User page to dialog
        self.addTab(self.user_attr_page, self.__tr('&User Attributes',
            'Title of the third dialog tab'))

        self.setOkButton(self.__tr('OK', 'A button label'))
        self.setCancelButton(self.__tr('Cancel', 'A button label'))

        # Connect signals to slots
        self.connect(self, qt.SIGNAL('applyButtonPressed()'),
            self.slotCheckAttributes)

        vitables.utils.customizeWidgetButtons(self)

        # Show the dialog
        self.show()


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('NodePropDlg', source, comment).latin1()


    def slotCheckAttributes(self):
        """
        Check the system attribute ``TITLE`` and the user attributes table.
        """

        if self.mode != 'r':
            self.updateTitle()
            # If any of the Add/Delete buttons was clicked previously
            # then check the user attributes
            if self.user_attr_page.user_attr_edited:
                self.checkUserAttributes()


    def updateTitle(self):
        """
        Update the ``TITLE`` system attribute if needed.
        
        This method takes advantage of the fact that the only editable
        cell of the system attributes table can be precisely that cell
        containing the ``TITLE`` value.
        """

        # Cell editing ends when Enter key is pressed. If the OK button
        # is pressed before cell editing ends then the transfers chain
        # editor contents --> qt.QTableItem --> cell is broken and the
        # attributes table is not properly updated. To avoid it we end
        # cell editing explicitely
        attr_table = self.sys_attr_page.getAttrTable()
        if attr_table.isEditing():
            attr_table.endEdit(attr_table.currEditRow(), 1, 1, 1)

        # Update the TITLE system attribute (if any)
        # new_title is a Python string self.asi.TITLE is a numpy.string_
        new_title = self.sys_attr_page.getTitleAttr()
        if hasattr(self.asi, 'TITLE') and self.asi.TITLE != new_title:
            setattr(self.asi, 'TITLE', new_title)


    def checkUserAttributes(self):
        """
        Check the user attributes table.

        If empty or repeated names, values mismatching the
        attribute type or out of range values are found then nothing
        is done. If the table is OK the node `ASI` is updated and the
        Properties dialog is closed.
        """

        # Error message for mismatching value/type pairs
        dtype_error = self.__tr("""\nError: "%s" value """
            """mismatches its data type.""",
            'User attributes table editing error')

        # Error message for out of range values
        range_error = self.__tr("""\nError: "%s" value """
            """is out of range.""",
            'User attributes table editing error')

        # Error message for syntax errors in Python attributes
        syntax_error = self.__tr("""\nError: "%s" """
            """cannot be converted to a Python object.""",
            'User attributes table editing error')

        attr_table = self.user_attr_page.getAttrTable()
        rows_range = range(0, attr_table.numRows())

        # Cell editing ends when Enter key is pressed. If the OK button
        # is pressed before cell editing ends then the transfers chain
        # editor contents --> qt.QTableItem --> cell is broken and the
        # attributes table is not properly updated. To avoid it we end
        # cell editing explicitely
        if attr_table.isEditing():
            for row in rows_range:
                attr_table.endEdit(row, 0, 1, 1)
                attr_table.endEdit(row, 1, 1, 1)

        # Check for empty Name cells
        for row in rows_range:
            if not attr_table.text(row, 0).latin1():
                self.attrs_are_ok = False
                self.user_attr_page.cc_display.setText(
                    self.__tr("""\nError: empty field Name in the row |%i|""", 
                        'User attributes table editing error') % int(row + 1))
                self.user_attr_page.cc_display.home(False)

        # Check for repeated names
        names_list = []
        for row in rows_range:
            name = attr_table.text(row, 0).latin1()
            if not name in names_list:
                names_list.append(name)
            else:
                self.attrs_are_ok = False
                self.user_attr_page.cc_display.setText(
                    self.__tr("""\nError: attribute name "%s" is repeated.""",
                        'User attributes table editing error') % name)
                self.user_attr_page.cc_display.home(False)

        # ViTables doesn't support editing ND-array attributes so they
        # are removed from the user attributes table. These attributes
        # can be found by reading them and inspecting its shape but it
        # is easier to locate them by inspecting the table cell properties
        rows_range.reverse()
        nd_attrs = sets.Set()
        for row in rows_range:
            if attr_table.isRowReadOnly(row):
                nd_attrs.add(attr_table.text(row, 0).latin1())
                attr_table.removeRow(row)
        attr_table.update()

        # Check for dtype, range and syntax correctness of scalar attributes
        for row in range(0, attr_table.numRows()):
            name = attr_table.text(row, 0).latin1()
            str_value =  attr_table.text(row, 1).latin1()
            dtype = attr_table.item(row, 2).currentText().latin1()
            if dtype != 'Python':
                # Format properly the string representation of value
                value = formatStrValue(dtype, str_value)
                if value is None :
                    self.attrs_are_ok = False
                    self.user_attr_page.cc_display.setText(dtype_error % name)
                    self.user_attr_page.cc_display.home(False)
                # Check if values are out of range
                else:
                    try:
                        value = checkOverflow(dtype, value)
                        numpy.array(value).astype(dtype) [()]
                    except IndexError:
                        self.attrs_are_ok = False
                        self.user_attr_page.cc_display.setText(range_error % name)
                        self.user_attr_page.cc_display.home(False)
                    except ValueError:
                        self.attrs_are_ok = False
                        self.user_attr_page.cc_display.setText(dtype_error % name)
                        self.user_attr_page.cc_display.home(False)
            # Check the syntax of the Python expression
            elif not checkSyntax(str_value):
                self.attrs_are_ok = False
                self.user_attr_page.cc_display.setText(syntax_error % name)
                self.user_attr_page.cc_display.home(False)

        # If table contents are OK then update the node attributes
        if self.attrs_are_ok:
            self.updateUserAttributes(nd_attrs)


    def updateUserAttributes(self, nd_attrs):
        """
        Update user attributes.

        If the user attributes have been edited the attribute set instance
        of the node being inspected must be updated.
        This method is called by checkUserAttributes only when the
        file has been opened in read write mode.
        
        :Parameter nd_attrs: the set of ND-array attributes
        """

        # Remove all scalar attributes. It ensures that, when renaming
        # an attribute, the old attribute is deleted.
        all_attrs = sets.Set(self.asi._v_attrnamesuser)
        for attr in (all_attrs - nd_attrs):
            try:
                self.asi._v_node._f_delAttr(attr)
            except:
                vitables.utils.formatExceptionInfo()

        # Set the user attributes from scratch using the attributes table
        # Note that ND-array attributes have been deleted from the table
        # Hint: if update doesn't refresh properly the table content then
        # use setCellContentFromEditor
        attr_table = self.user_attr_page.getAttrTable()
        attr_table.update()

        for row in range(0, attr_table.numRows()):
            # Scalar attributes are stored as
            # numpy scalar arrays of the proper type
            dtype = attr_table.item(row, 2).currentText().latin1()
            name = attr_table.text(row, 0).latin1()
            value =  formatStrValue(dtype, attr_table.text(row, 1).latin1())

            if dtype == 'Python':
                value =  attr_table.text(row, 1).latin1()
                if (value[0], value[-1]) in [("'", "'"), ('"', '"')]:
                    value = eval('\"%s\"' % value)
                else:
                    value = eval('%s' % value)
            else:
                value = numpy.array(value).astype(dtype)

            # Updates the ASI
            try:
                setattr(self.asi, name, value)
            except:
                vitables.utils.formatExceptionInfo()


    def accept(self):
        """
        Customised slot for accepted dialogs.

        This is an overwritten method.
        This SLOT is always the last called method whenever the
        apply/ok buttons are pressed.
        """

        # If the attributes pass correctness checks then close the dialog
        if self.attrs_are_ok:
            qt.QTabDialog.accept(self)
        # If not then keep the dialog opened *and reset the attr_are_ok flag*
        else:
            self.attrs_are_ok = True

