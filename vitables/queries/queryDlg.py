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

"""
Here is defined the QueryDlg class.

Classes:

* QueryDlg(QDialog)

Methods:

* __init__(self, info, ft_names, counter, initial_query, table)
* __tr(self,  source, comment=None)
* slotEnableIndicesColumn(self, cb_on)
* slotInsertOperator(self, operator)
* slotInsertField(self, field_id)
* slotInsertFunction(self, text)
* slotUpdateOKState(self)
* checkConditionSyntax(self, condition)
* slotAccept(self)

Functions:

* slotEnterHelpMode()

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'QueryDlg'

import numpy

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.queries import queryUI

class QueryDlg(QtGui.QDialog, queryUI.Ui_QueryDialog):
    """
    A dialog for filter creation .

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
    """

    def __init__(self, info, ft_names, counter, initial_query, table):
        """
        Ctor.

        :Parameters:

        - `info`: a dictionary with information about the table being queried
        - `ft_names`: the list of filtered tables names currently in use
        - `counter`: a counter used to give a unique ID to the query
        - `initial_query`: the dialog will be setup with this query (if any)
        - `table`: the table being queried
        """

        #
        # Create the dialog and customise the content of some widgets
        #
        QtGui.QDialog.__init__(self, QtGui.qApp.activeWindow())
        self.setupUi(self)

        self.setWindowTitle(self.__tr('New query on table: %s',
            'A dialog caption') % info[u'name'])

        self.name_le.setText('FilteredTable_%s' % counter)

        self.indices_column.setEnabled(0)

        # Use the values of the last query done on this table (if any)
        if initial_query != '':
            self.query_le.setText(initial_query)

        # Fill the combos
        operators = [u'&', u'|', u'~', u'<', u'<=', u'==', u'!=', u'>', u'>=', u'+',
            u'-', u'*', u'/', u'**', u'%']
        self.operators_cb.insertItems(0, QtCore.QStringList(operators))
        functions = [u'where', u'sin', u'cos', u'tan', u'arcsin', u'arccos', 
            u'arctan', u'arctan2', u'sinh', u'cosh', u'tanh', 
            u'arcsinh', u'arccosh', u'arctanh', u'log', u'log10', u'log1p', 
            u'exp', u'expm1', u'sqrt', 
            u'real', u'imag', u'complex']
        self.functions_cb.insertItems(0, QtCore.QStringList(functions))
        sorted_fields = [field for field in info[u'valid_fields']]
        sorted_fields.sort()
        self.columns_cb.insertItems(0, QtCore.QStringList(sorted_fields))
        self.rstop.setText(u'%s' % info[u'nrows'])

        whatsthis_button = self.button_box.button(QtGui.QDialogButtonBox.Help)
        whatsthis_button.setText("&What's this")

        #
        # Setup a validator for Range selectors section
        #
        validator = QtGui.QRegExpValidator(QtCore.QRegExp("\\d*"), self)
        self.rstart.setValidator(validator)
        self.rstop.setValidator(validator)
        self.rstep.setValidator(validator)

        #
        # Attributes used by method slotUpdateOKState
        #
        self.used_names = ft_names
        self.col_names = info[u'col_names']
        self.condvars = info[u'condvars']
        self.source_table = table
        self.num_rows = info[u'nrows']

        #
        # Attributes used by method slotAccept
        #
        # If the dialog is cancelled these initial values will be returned to
        # the caller. If the dialog is accepted then these values will be
        # updated (in the slotAccept method) and returned to the caller
        self.query_info = {}
        self.query_info[u'condition'] = u''
        self.query_info[u'rows_range'] = ()
        self.query_info[u'ft_name'] = u''
        self.query_info[u'indices_field_name'] = u''
        self.query_info[u'condvars'] = self.condvars
        self.query_info[u'src_filepath'] = info[u'src_filepath']
        self.query_info[u'src_path'] = info[u'src_path']

        #
        # Connect signals to slots
        #
        activated = QtCore.SIGNAL('activated(const QString &)')
        text_changed = QtCore.SIGNAL('textChanged(const QString &)')
        self.connect(self.name_le, text_changed, self.slotUpdateOKState)
        self.connect(self.indices_checkbox, QtCore.SIGNAL('toggled(bool)'),
            self.slotEnableIndicesColumn)
        self.connect(self.indices_column, text_changed, self.slotUpdateOKState)
        self.connect(self.query_le, text_changed, self.slotUpdateOKState)
        self.connect(self.rstart, text_changed, self.slotUpdateOKState)
        self.connect(self.rstop, text_changed, self.slotUpdateOKState)
        self.connect(self.columns_cb, activated, self.slotInsertField)
        self.connect(self.operators_cb, activated, self.slotInsertOperator)
        self.connect(self.functions_cb, activated, self.slotInsertFunction)
        self.connect(self.button_box, QtCore.SIGNAL('helpRequested()'),
            QtGui.QWhatsThis.enterWhatsThisMode)
        self.connect(self.button_box, QtCore.SIGNAL('accepted()'), 
            self.slotAccept)
        self.connect(self.button_box, QtCore.SIGNAL('rejected()'),
            QtCore.SLOT('reject()'))
        # Ensure that if the condition line edit is initialised with an
        # initial condition then the OK button will be enabled
        self.name_le.emit(text_changed, self.name_le.text())


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(QtGui.qApp.translate(_context, source, comment))


    def slotEnableIndicesColumn(self, cb_on):
        """
        Enable/disable the indices column name field.

        If the checkbox in the global options groupbox is down then
        a column with the indices of the filtered rows will be added
        to the table produced by the filtering process. Moreover the
        user can set the name of this column.

        :Parameter cb_on: a boolean that indicates if the checkbox is down or not.
    """

        if cb_on:
            self.indices_column.setEnabled(1)
        else:
            self.indices_column.setEnabled(0)


    def slotInsertOperator(self, operator):
        """
        Insert an operator in the query line editor.

        :Parameter operator: is the operator in the combobox current item
        """
        self.query_le.insert(u' %s ' % operator)


    def slotInsertField(self, field_id):
        """
        Insert a fieldname in the query line editor.

        When the fields combobox is activated the selected field_id is
        inserted in the query line editor. Fields whose names contain
        blanks have a field id with the format 'condvar (fieldname)'.
        In this case only the condvar name will be inserted in the query
        line editor.

        :Parameter field_id: is the field identifier in the combobox current item
        """
        self.query_le.insert(field_id.split(u' ')[0])


    def slotInsertFunction(self, text):
        """
        Update  the contents of the query line editor.

        When the functions combobox is activated the selected value is
        inserted in the query line editor.

        :Parameter text: is the text of the combobox current item
        """

        name2call = {u'where': u'where(B, N, N)', 
            u'sin': u'sin(F|C)', 
            u'cos': u'cos(F|C)', 
            u'tan': u'tan(F|C)', 
            u'arcsin': u'arcsin(F|C)', 
            u'arccos': u'arccos(F|C)', 
            u'arctan': u'arctan(F|C)', 
            u'arctan2': u'arctan2(F, F)', 
            u'sinh': u'sinh(F|C)', 
            u'cosh': u'cosh(F|C)', 
            u'tanh': u'tanh(F|C)', 
            u'arcsinh': u'arcsinh(F|C)', 
            u'arccosh': u'arccosh(F|C)', 
            u'arctanh': u'arctanh(F|C)', 
            u'log': u'log(F|C)', 
            u'log10': u'log10(F|C)', 
            u'log1p': u'log1p(F|C)', 
            u'exp': u'exp(F|C)', 
            u'expm1': u'expm1(F|C)', 
            u'sqrt': u'sqrt(F|C)', 
            u'real': u'real(C)', 
            u'imag': u'imag(C)', 
            u'complex': u'complex(F, F)'
            }
        self.query_le.insert(name2call[unicode(text)])


    def slotUpdateOKState(self):
        """
        Update the activation state of the OK button.

        Every time that the table name text box changes the new
        content is checked. If it is empty, then the OK button is
        disabled.
        Every time that the indices column name text box changes the
        new content is checked. If it is empty, then the OK button
        is disabled.
        Every time that the lower/upper limit text box change the
        new content is checked. If the new values don't make a legal
        condition, then the OK button is disabled.
        Every time the column name combobox changes the datatype
        of limit values is checked. If there is a mismatch, then the
        OK button is disabled.
        Every time that the spinboxes content change the new content
        is checked. If the combination of the start/stop/step boxes
        makes a not legal selection range, then the OK button is
        disabled.
        """

        status_ok = True

        # Check the table name
        ft_name = unicode(self.name_le.text())
        if not ft_name:
            status_ok = False
        elif ft_name in self.used_names:
            status_ok = False
            print self.__tr("""The chosen name is already in use. Please,"""
                """ choose another one.""", 'A logger info message')

        # Check the indices column name
        indices_colname = unicode(self.indices_column.text())
        if self.indices_column.isEnabled():
            if indices_colname == '':
                status_ok = False
                print self.__tr("""Enter a name for the column of indices, """
                    """please.""",
                    'A logger info message')
            elif indices_colname.count('/'):
                status_ok = False
                print self.__tr("""The chosen name for the column of indices"""
                    """is not valid. It contains '/' characters""",
                    'A logger info message')
            elif indices_colname in self.col_names:
                status_ok = False
                print self.__tr("""The chosen name for the column of indices"""
                    """ is already in use. Please, choose another one.""",
                    'A logger info message')

        # Check the condition.
        # If it is an empty string the OK button is not enabled
        condition = unicode(self.query_le.text())
        if condition.isspace() or (condition in [None, u'']):
            status_ok = False

        # Check the range values
        start_str = unicode(self.rstart.text())
        stop_str = unicode(self.rstop.text())
        if not (start_str and stop_str):
            status_ok = False
        else:
            start = numpy.array(start_str).astype(numpy.int64)
            stop = numpy.array(stop_str).astype(numpy.int64)
            if stop > self.num_rows:
                status_ok = False
                print self.__tr("""The stop value is greater than the number"""
                                """ of rows. Please, choose another one.""",
                                'A logger info message')
            elif start > stop:
                status_ok = False
                print self.__tr("""The start value is greater than the """
                                """stop value. Please, choose another one.""",
                                'A logger info message')
            elif start < 1:
                status_ok = False
                print self.__tr("""The start value must be greater than 0.""", 
                                'A logger info message')

        # Enable/disable the OK button
        ok_button = self.button_box.button(QtGui.QDialogButtonBox.Ok)
        if status_ok:
            ok_button.setEnabled(1)
        else:
            ok_button.setEnabled(0)


    def checkConditionSyntax(self, condition):
        """Check the condition syntax."""

        syntax_ok = True
        try:
            self.source_table.willQueryUseIndexing(condition, self.condvars)
        except SyntaxError, error:
            syntax_ok = False
            print self.__tr("""\nError: %s""",
                'A logger info message') % error.__doc__
            vitables.utils.formatExceptionInfo()
        except NameError, error:
            syntax_ok = False
            print self.__tr("""\nError: %s""",
                'A logger info message') % error.__doc__
            vitables.utils.formatExceptionInfo()
        except ValueError, error:
            syntax_ok = False
            print self.__tr("""\nError: %s""",
                'A logger info message') % error.__doc__
            vitables.utils.formatExceptionInfo()
        except TypeError, error:
            syntax_ok = False
            print self.__tr("""\nError: %s""",
                'A logger info message') % error.__doc__
            vitables.utils.formatExceptionInfo()
        except:
            syntax_ok = False
            vitables.utils.formatExceptionInfo()
        return syntax_ok


    def slotAccept(self):
        """Compose the query and return."""

        # Get the query
        condition = unicode(self.query_le.text())
        # Blanks at the begining of condition raise a SyntaxError
        condition = condition.strip()
        if not self.checkConditionSyntax(condition):
            return

        self.query_info[u'condition'] = condition

        # Get the table name and the name of the column with indices (if any)
        self.query_info[u'ft_name'] = unicode(self.name_le.text())
        if self.indices_column.isEnabled():
            self.query_info[u'indices_field_name'] = \
                unicode(self.indices_column.text())

        # Get the range and convert it into a Python range
        self.query_info[u'rows_range'] = (
           numpy.array(unicode(self.rstart.text())).astype(numpy.int64) - 1,
           numpy.array(unicode(self.rstop.text())).astype(numpy.int64),
           numpy.array(unicode(self.rstep.text())).astype(numpy.int64))

        # Exit
        self.accept()
