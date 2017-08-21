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
This module provides a dialog for querying (filtering) `tables.Table` nodes.
The result of the query is stored in other `tables.Table` node, referred as a
filtered table, which will live in the temporary database (labeled as `Query
results` in the databases tree).
"""

import logging
import os.path
import vitables.utils

import numpy
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy.uic import loadUiType


__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate

# This method of the PyQt5.uic module allows for dinamically loading user
# interfaces created by QtDesigner. See the PyQt5 Reference Guide for more
# info.
Ui_QueryDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__), 'query_dlg.ui'))[0]

log = logging.getLogger(__name__)


class QueryDlg(QtWidgets.QDialog, Ui_QueryDialog):
    """
    A dialog for filtering `tables.Table` nodes.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    The dialog layout looks like this::

        root
            label + textbox
            checkbox + label + textbox
            text box
            combobox + combobox + combobox
            label + textbox
            label + textbox
            label + textbox
            Ok + Cancel

    A text box is used to enter the condition to be applied. Combos
    are used to enter operators, functions and field names. Textboxes
    are used to enter the range of the query.

    :Parameters:

    - `info`: a dictionary with information about the table being queried
    - `ft_names`: the list of filtered tables names currently in use
    - `counter`: a counter used to give a unique ID to the query
    - `initial_query`: the dialog will be setup with this query (if any)
    - `table`: the table being queried
    """

    def __init__(self, info, ft_names, counter, initial_query, table):
        """
        Initialise the dialog.
        """
        #
        # Attributes used by slot updateOKState
        #
        self.used_names = ft_names
        self.col_names = info['col_names']
        self.condvars = info['condvars']
        self.source_table = table
        self.num_rows = info['nrows']

        #
        # Attributes used by slot composeQuery
        #
        # If the dialog is cancelled these initial values will be returned to
        # the caller. If the dialog is accepted then these values will be
        # updated (in the slotAccept method) and returned to the caller
        self.query_info = {}
        self.query_info['condition'] = ''
        self.query_info['rows_range'] = ()
        self.query_info['ft_name'] = ''
        self.query_info['indices_field_name'] = ''
        self.query_info['condvars'] = self.condvars
        self.query_info['src_filepath'] = info['src_filepath']
        self.query_info['src_path'] = info['src_path']

        #
        # Create the dialog and customise the content of some widgets
        #
        super(QueryDlg, self).__init__(QtWidgets.qApp.activeWindow())
        self.setupUi(self)

        self.setWindowTitle(translate('QueryDlg', 'New query on table: {0}',
                                      'A dialog caption').format(info['name']))

        self.nameLE.setText('FilteredTable_{0}'.format(counter))

        self.indicesColumnLE.setEnabled(0)

        # Use the values of the last query done on this table (if any)
        if initial_query != '':
            self.queryLE.setText(initial_query)

        # Fill the combos
        operators = ['&', '|', '~', '<', '<=', '==', '!=', '>', '>=',
                     '+', '-', '*', '/', '**', '%']
        self.operatorsComboBox.insertItems(0, operators)
        functions = ['where', 'sin', 'cos', 'tan', 'arcsin', 'arccos',
                     'arctan', 'arctan2', 'sinh', 'cosh', 'tanh',
                     'arcsinh', 'arccosh', 'arctanh', 'log', 'log10', 'log1p',
                     'exp', 'expm1', 'sqrt', 'real', 'imag', 'complex']
        self.functionsComboBox.insertItems(0, functions)
        sorted_fields = [field for field in info['valid_fields']]
        sorted_fields.sort()
        self.columnsComboBox.insertItems(0, sorted_fields)
        self.rstartLE.setText('0')
        self.rstopLE.setText('{0}'.format(info['nrows']))

        whatsthis_button = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Help)
        whatsthis_button.setText("&What's this")

        #
        # Setup a validator for Range selectors section
        #
        validator = QtGui.QRegExpValidator(QtCore.QRegExp("\\d*"), self)
        self.rstartLE.setValidator(validator)
        self.rstopLE.setValidator(validator)
        self.rstep.setValidator(validator)

        #
        # Connect signals to slots
        #
        self.buttonBox.helpRequested.connect(
            QtWidgets.QWhatsThis.enterWhatsThisMode)
        # Ensure that if the condition line edit is initialised with an
        # initial condition then the OK button will be enabled
        self.nameLE.textChanged.emit(self.nameLE.text())

    @QtCore.Slot(bool, name="on_indicesCheckBox_toggled")
    def enableIndicesColumn(self, cb_on):
        """
        Enable/disable the indices column name field.

        If the checkbox in the global options groupbox is checked then
        a column with the indices of the filtered rows will be added
        to the table produced by the filtering process. Moreover the
        user can set the name of this column.

        :Parameter cb_on: a boolean that indicates if the checkbox is down
            or not.
        """

        if cb_on:
            self.indicesColumnLE.setEnabled(1)
        else:
            self.indicesColumnLE.setEnabled(0)

    @QtCore.Slot("QString", name="on_operatorsComboBox_activated")
    def insertOperator(self, operator):
        """
        Insert an operator in the query line editor.

        :Parameter operator: is the operator in the combobox current item
        """
        self.queryLE.insert(' {0} '.format(operator))

    @QtCore.Slot("QString", name="on_columnsComboBox_activated")
    def insertField(self, field_id):
        """
        Insert a fieldname in the query line editor.

        When the fields combobox is activated the selected field_id is
        inserted in the query line editor. Fields whose names contain
        blanks have a field id with the format 'condvar (fieldname)'.
        In this case only the condvar name will be inserted in the query
        line editor.

        :Parameter field_id: is the field identifier in the combobox current
            item
        """
        self.queryLE.insert(field_id.split(' ')[0])

    @QtCore.Slot("QString", name="on_functionsComboBox_activated")
    def insertFunction(self, text):
        """
        Insert a function in the query line editor.

        When the functions combobox is activated the selected value is
        inserted in the query line editor.

        :Parameter text: is the text of the combobox current item
        """

        name2call = {'where': 'where(B, N, N)',
                     'sin': 'sin(F|C)',
                     'cos': 'cos(F|C)',
                     'tan': 'tan(F|C)',
                     'arcsin': 'arcsin(F|C)',
                     'arccos': 'arccos(F|C)',
                     'arctan': 'arctan(F|C)',
                     'arctan2': 'arctan2(F, F)',
                     'sinh': 'sinh(F|C)',
                     'cosh': 'cosh(F|C)',
                     'tanh': 'tanh(F|C)',
                     'arcsinh': 'arcsinh(F|C)',
                     'arccosh': 'arccosh(F|C)',
                     'arctanh': 'arctanh(F|C)',
                     'log': 'log(F|C)',
                     'log10': 'log10(F|C)',
                     'log1p': 'log1p(F|C)',
                     'exp': 'exp(F|C)',
                     'expm1': 'expm1(F|C)',
                     'sqrt': 'sqrt(F|C)',
                     'real': 'real(C)',
                     'imag': 'imag(C)',
                     'complex': 'complex(F, F)'}
        self.queryLE.insert(name2call[text])

    @QtCore.Slot("QString", name="on_nameLE_textChanged")
    @QtCore.Slot("QString", name="on_indicesColumnLE_textChanged")
    @QtCore.Slot("QString", name="on_queryLE_textChanged")
    @QtCore.Slot("QString", name="on_rstartLE_textChanged")
    @QtCore.Slot("QString", name="on_rstopLE_textChanged")
    def updateOKState(self):
        """
        Update the activation state of the `OK` button.

        Every time that the table name text box changes the new
        content is checked. If it is empty, then the `OK` button is
        disabled.
        If the indices checkbox is checked, every time that the indices column
        name text box changes the
        new content is checked. If it is empty, then the `OK` button
        is disabled.
        Every time that the lower/upper limit text box change the
        new content is checked. If the new values don't make a legal
        condition, then the `OK` button is disabled.
        Every time the column name combobox changes the datatype
        of limit values is checked. If there is a mismatch, then the
        `OK` button is disabled.
        Every time that the spinboxes content change the new content
        is checked. If the combination of the start/stop/step boxes
        makes a not legal selection range, then the `OK` button is
        disabled.
        """

        status_ok = True

        # Check the table name
        ft_name = self.nameLE.text()
        if not ft_name:
            status_ok = False
        elif ft_name in self.used_names:
            status_ok = False
            log.error(
                translate('QueryDlg',
                          """The chosen name is already in use. Please,"""
                          """ choose another one.""",
                          'A logger info message'))

        # Check the indices column name
        indices_colname = self.indicesColumnLE.text()
        if self.indicesColumnLE.isEnabled():
            if indices_colname == '':
                status_ok = False
                log.error(
                    translate('QueryDlg',
                              "Enter a name for the column of indices, please",
                              'A logger info message'))
            elif indices_colname.count('/'):
                status_ok = False
                log.error(
                    translate('QueryDlg',
                              """The chosen name for the column of indices"""
                              """is not valid. It contains '/' characters""",
                              'A logger info message'))
            elif indices_colname in self.col_names:
                status_ok = False
                log.error(
                    translate('QueryDlg',
                              """The chosen name for the column of indices"""
                              """ is already in use. """
                              """"Please, choose another one.""",
                              'A logger info message'))

        # Check the condition.
        # If it is an empty string the OK button is not enabled
        condition = self.queryLE.text()
        if condition.isspace() or (condition in [None, '']):
            status_ok = False

        # Check the range values
        start_str = self.rstartLE.text()
        stop_str = self.rstopLE.text()
        if not (start_str and stop_str):
            status_ok = False
        else:
            start = numpy.array(start_str).astype(numpy.int64)
            stop = numpy.array(stop_str).astype(numpy.int64)
            if stop > self.num_rows:
                status_ok = False
                log.error(
                    translate('QueryDlg',
                              """The stop value cannot be greater than """
                              """the number of rows.""",
                              'A logger info message'))
            elif start > stop:
                status_ok = False
                log.error(
                    translate('QueryDlg',
                              """The start value cannot be greater than the """
                              """stop value.""",
                              'A logger info message'))

        # Enable/disable the OK button
        ok_button = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        if status_ok:
            ok_button.setEnabled(1)
        else:
            ok_button.setEnabled(0)

    def checkConditionSyntax(self, condition):
        """Check the condition syntax.

        :Parameter condition: the query condition used for filtering the table
        """

        syntax_ok = True
        try:
            self.source_table.will_query_use_indexing(condition, self.condvars)
        except SyntaxError as error:
            syntax_ok = False
            log.error(error.__doc__)
            vitables.utils.formatExceptionInfo()
        except NameError as error:
            syntax_ok = False
            log.error(error.__doc__)
            vitables.utils.formatExceptionInfo()
        except ValueError as error:
            syntax_ok = False
            log.error(error.__doc__)
            vitables.utils.formatExceptionInfo()
        except TypeError as error:
            syntax_ok = False
            log.error(error.__doc__)
            vitables.utils.formatExceptionInfo()
        except:
            syntax_ok = False
            vitables.utils.formatExceptionInfo()
        return syntax_ok

    @QtCore.Slot(name="on_buttonBox_accepted")
    def composeQuery(self):
        """Slot for composing the query and accept the dialog."""

        # Get the query
        condition = self.queryLE.text()
        # Blanks at the begining of condition raise a SyntaxError
        condition = condition.strip()
        if not self.checkConditionSyntax(condition):
            return

        self.query_info['condition'] = condition

        # Get the table name and the name of the column with indices (if any)
        self.query_info['ft_name'] = self.nameLE.text()
        if self.indicesColumnLE.isEnabled():
            self.query_info['indices_field_name'] = \
                self.indicesColumnLE.text()

        # Get the range and convert it into a Python range
        self.query_info['rows_range'] = (
            numpy.array(self.rstartLE.text()).astype(numpy.int64),
            numpy.array(self.rstopLE.text()).astype(numpy.int64),
            numpy.array(self.rstep.text()).astype(numpy.int64))

        # Exit
        self.accept()
