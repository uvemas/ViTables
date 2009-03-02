#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
* makeSectionOne(self, global_opt_gb)
* makeSectionTwo(self, condition_gb, valid_fields)
* makeSectionThree(self, rows_range_gb, nrows)
* makeSectionFour(self, buttons_layout)
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import vitables.utils

class QueryDlg(QDialog):
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

        # Makes the attributes edition dialog and gives it a layout
        QDialog.__init__(self, qApp.activeWindow())
        dlg_layout = QVBoxLayout(self)
        dlg_layout.setSpacing(6)
        self.setWindowTitle(self.__tr('New query on table: %s',
            'A dialog caption') % info[u'name'])

        # Attributes used by method slotUpdateOKState
        self.used_names = ft_names
        self.col_names = info[u'col_names']
        self.condvars = info[u'condvars']
        self.source_table = table
        self.num_rows = info[u'nrows']

        # Attributes used by method slotAccept
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

        # Main widgets
        # Global Options section
        global_opt_gb = QGroupBox(self.__tr('Global options',
            'A groupbox title'), self)
        dlg_layout.addWidget(global_opt_gb)
        # Table name text box
        self.name_le = QLineEdit('FilteredTable_%s' % counter, 
                                        global_opt_gb)
        self.name_le.setWhatsThis(self.__tr(
            """<qt>
            The name of the table where the query results will be added.
            </qt>""",
            'A help text for the Query dialog'))
        # Indices field name widgets
        self.indices_checkbox = QCheckBox(global_opt_gb)
        self.indices_column = QLineEdit('Orig_idx', global_opt_gb)
        self.indices_column.setWhatsThis(self.__tr(
            """<qt>
            The name of the column where the indices of the selected rows
            will be added.
            </qt>""",
            'A help text for the Query dialog')
            )
        # Condition section
        condition_gb = QGroupBox(self.__tr('Query condition',
            'A groupbox title'), self)
        dlg_layout.addWidget(condition_gb)
        self.query_le = QLineEdit(condition_gb)
        self.query_le.setWhatsThis(self.__tr(
            """<qt>
            <h3>Conditions syntax</h3>
            A condition on a table is just a <em>string</em> containing a
            Python expression that involves <em>at least one column</em>
            , and maybe some constants and external variables, all combined
            with algebraic operators or functions.
            Beware that <tt>&</tt>, <tt>|</tt> and <tt>~</tt> operators
            are used for logical comparisons. They have higher precedence
            than logical operators so we recommend to <em>always use
            parenthesis around logical operators</em>.</p>
            <p>The following table shows some examples of conditions and
            their equivalent Python expressions.</p>
            <div align='center'><table border='1'>
            <tr><th>Condition</th><th>Python expression</th></tr>
            <tr><td><code>a & (b == c)</code></td>
            <td><code>a and b == c</code></td></tr>
            <tr><td><code>(0 &lt; x) & (x &lt; 1)</code></td>
            <td><code>0 &lt; x &lt; 1</code></td></tr>
            <tr><td><code>a + b  &gt; c</code></td>
            <td><code>a + b  &gt; c</code></td></tr>
            <tr><td><code>where(a > b, 3, 4)</code></td>
            <td></td></tr>
            </table></div>
            <p>You can find detailed information about conditions in the
            Appendix B of the PyTables users guide.</p>
            </qt>""",
            'A help text for the Query dialog')
        )
        self.operators_cb = QComboBox(condition_gb)
        self.operators_cb.setWhatsThis(self.__tr(
            """<qt>
            The operators that can be used in a given condition. Operators
            can be logical, comparison and arithmetic.<br>Not all operators
            are available for every data type.
            </qt>""",
            'A help text for the Query dialog')
            )
        self.functions_cb = QComboBox(condition_gb)
        self.functions_cb.setWhatsThis(self.__tr(
            """<qt>
            The set of functions that can appear in a condition.
            It includes functions for doing selections, trigonometric
            functions and functions on complex numbers. For ease
            of use, arguments are automatically included when a
            function is inserted. The arguments meaning is:
            <ul><li>N: number</li><li>B: boolean</li>
            <li>F: float</li><li>C: complex</li></ul>
            </qt>""",
            'A help text for the Query dialog')
            )
        self.columns_cb = QComboBox(condition_gb)
        self.columns_cb.setEditable(False)
        self.columns_cb.setWhatsThis(self.__tr(
            """<qt>
            The names of the searchable columns. They must
            fulfill the following requirements:
            <ul><li>must be not nested</li>
            <li>must have a scalar data type</li>
            <li>their data type cannot be <code>complex</code></li></ul>
            Columns whose names contains blanks are automatically mapped
            to variables whose names contain no blanks. For querying
            those columns the mapped variables will be used.
            </qt>""",
            'A help text for the Query dialog')
            )
        # Range selectors section
        rows_range_gb = \
            QGroupBox(self.__tr('Range of rows', 'A groupbox title'), 
                            self)
        rows_range_gb.setWhatsThis(self.__tr(
            """The range of rows included in the query.""",
            'A help text for the Query dialog')
            )
        dlg_layout.addWidget(rows_range_gb)
        self.rstart = QLineEdit('', rows_range_gb)
        self.rstop = QLineEdit('', rows_range_gb)
        self.rstep = QLineEdit('', rows_range_gb)
        validator = QRegExpValidator(QRegExp("\\d*"), self)
        self.rstart.setValidator(validator)
        self.rstop.setValidator(validator)
        self.rstep.setValidator(validator)
        # The OK and Cancel buttons section
        buttons_layout = QHBoxLayout()
        dlg_layout.addLayout(buttons_layout)
        buttons_layout.setSpacing(6)
        self.ok_button = \
            QPushButton(self.__tr('&OK', 'A button label'), self)
        self.cancel_button = \
            QPushButton(self.__tr('&Cancel', 'A button label'), self)
        self.help_button = \
            QPushButton(self.__tr("&What's This", 'Button label'), self)

        # Add components to dialog
        self.makeSectionOne(global_opt_gb)
        self.makeSectionTwo(condition_gb, info[u'valid_fields'])
        self.makeSectionThree(rows_range_gb, info[u'nrows'])
        self.makeSectionFour(buttons_layout)

        # Use the values of the last query done on this table (if any)
        if initial_query != '':
            self.query_le.setText(initial_query)

        # Connect signals to slots
        activated = SIGNAL('activated(const QString &)')
        text_changed = SIGNAL('textChanged(const QString &)')
        self.connect(self.name_le, text_changed, self.slotUpdateOKState)
        self.connect(self.indices_column, text_changed, self.slotUpdateOKState)
        self.connect(self.query_le, text_changed, self.slotUpdateOKState)
        self.connect(self.rstart, text_changed, self.slotUpdateOKState)
        self.connect(self.rstop, text_changed, self.slotUpdateOKState)
        self.connect(self.columns_cb, activated, self.slotInsertField)
        self.connect(self.operators_cb, activated, self.slotInsertOperator)
        self.connect(self.functions_cb, activated, self.slotInsertFunction)
        self.connect(self.help_button, SIGNAL('clicked()'),
            QWhatsThis.enterWhatsThisMode)
        self.connect(self.indices_checkbox, SIGNAL('toggled(bool)'),
            self.slotEnableIndicesColumn)
        self.connect(self.ok_button, SIGNAL('clicked()'), 
            self.slotAccept)
        self.connect(self.cancel_button, SIGNAL('clicked()'),
            SLOT('reject()'))
        # Ensure that if the condition line edit is initialised with an
        # initial condition then the OK button will be enabled
        self.name_le.emit(text_changed, self.name_le.text())


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate(_context, source, comment))


    def makeSectionOne(self, global_opt_gb):
        """
        Make the Global Options section.

        :Parameter global_opt_gb: the Global Options groupbox
        """

        # The table name area
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel(self.__tr('Name:', 
                                            'A textbox label'), 
                                            global_opt_gb))
        name_layout.addWidget(self.name_le)

        # The column with original indices area
        indices_layout = QHBoxLayout()
        self.indices_checkbox.setChecked(0)
        indices_layout.addWidget(self.indices_checkbox)
        indices_layout.addWidget(QLabel(\
            self.__tr('Original indices into column:',
            'A label in the Query-->New filter dialog'), global_opt_gb))
        self.indices_column.setEnabled(0)
        indices_layout.addWidget(self.indices_column)

        global_layout = QVBoxLayout()
        global_opt_gb.setLayout(global_layout)
        global_layout.addLayout(name_layout)
        global_layout.addLayout(indices_layout)


    def makeSectionTwo(self, condition_gb, valid_fields):
        """
        Make the Condition section.

        :Parameters:

        - `condition_gb`: the Condition groupbox
        - `valid_fields`: the set of searchable field names
        """

        # Add a horizontal layout to the groupbox layout. This new
        # layout contain the section combos
        combos_layout = QHBoxLayout()
        combos_layout.addStretch(1)
        combos_layout.addWidget(self.columns_cb)
        combos_layout.addWidget(self.operators_cb)
        combos_layout.addWidget(self.functions_cb)
        combos_layout.addStretch(1)

        condition_gb_layout = QVBoxLayout()
        condition_gb.setLayout(condition_gb_layout)
        condition_gb_layout.addWidget(self.query_le)
        condition_gb_layout.addLayout(combos_layout)

        # Fill the combos
        operators = [u'&', u'|', u'~', u'<', u'<=', u'==', u'!=', u'>', u'>=', u'+',
            u'-', u'*', u'/', u'**', u'%']
        self.operators_cb.insertItems(0, QStringList(operators))
        functions = [u'where', u'sin', u'cos', u'tan', u'arcsin', u'arccos', 
            u'arctan', u'arctan2', u'sinh', u'cosh', u'tanh', u'sqrt', 
            u'real', u'imag', u'complex']
        self.functions_cb.insertItems(0, QStringList(functions))
        sorted_fields = [field for field in valid_fields]
        sorted_fields.sort()
        self.columns_cb.insertItems(0, QStringList(sorted_fields))


    def makeSectionThree(self, rows_range_gb, nrows):
        """
        Make the Range Selectors section.

        :Parameters:

        - `rows_range_gb`: the Rows Range groupbox
        - `nrows`: the number of rows of the table being filtered
        """

        range_layout = QGridLayout(rows_range_gb)

        start_label = QLabel(self.__tr('Start:', 
                                   'A range selector label'),
                                   rows_range_gb)
        range_layout.addWidget(start_label, 0, 0)
        self.rstart.setText('1')
        range_layout.addWidget(self.rstart, 0, 1)

        stop_label = QLabel(self.__tr('Stop:', 'A range selector label'),
            rows_range_gb)
        range_layout.addWidget(stop_label, 1, 0)
        self.rstop.setText(u'%s' % nrows)
        range_layout.addWidget(self.rstop, 1, 1)

        step_label = QLabel(self.__tr('Step:', 'A range selector label'),
            rows_range_gb)
        range_layout.addWidget(step_label, 2, 0)
        self.rstep.setText(u'1')
        range_layout.addWidget(self.rstep, 2, 1)

        range_layout.setColumnStretch(2, 1)


    def makeSectionFour(self, buttons_layout):
        """
        Make the dialog buttons section.

        :Parameter buttons_layout: the layout where buttons are added
        """

        buttons_layout.addStretch(1)
        self.ok_button.setEnabled(0)
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.help_button)
        buttons_layout.addStretch(1)


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
        if status_ok:
            self.ok_button.setEnabled(1)
        else:
            self.ok_button.setEnabled(0)


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
