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
#       $Id: queryDlg.py 1020 2008-03-28 16:41:24Z vmas $
#
########################################################################

"""
Here is defined the QueryDlg class.

Classes:

* QueryDlg(qt.QDialog)

Methods:

* __init__(self, query_info, info, ft_names, counter, initial_query, qtable)
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

import numpy

import tables.exceptions

import qt

import vitables.utils

def slotEnterHelpMode():
    """Makes the dialog to enter in help mode."""
    qt.QWhatsThis.enterWhatsThisMode()


class QueryDlg(qt.QDialog):
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
    are used to enter operators, functions and field names.
    """


    def __init__(self, query_info, info, ft_names, counter, initial_query, qtable):
        """
        Ctor.

        :Parameters:

        - `query_info`: a dictionary with information about the query itself
        - `info`: a dictionary with information about the table being queried
        - `ft_names`: the list of filtered tables names currently in use
        - `counter`: a counter used to give a unique ID to the query
        - `initial_query`: the dialog will be setup with this query (if any)
        - `qtable`: the table being queried
        """

        # Makes the New Query dialog and gives it a layout
        qt.QDialog.__init__(self, qt.qApp.mainWidget())
        dlg_layout = qt.QVBoxLayout(self, 10, 6)
        self.setCaption(self.__tr('New query on table: %s',
            'A dialog caption') % info['name'])

        # Attributes used by method slotUpdateOKState
        self.used_names = ft_names
        self.col_names = info['col_names']
        self.num_rows = info['nrows']
        self.source_table = qtable
        self.condvars = info['condvars']

        # Attributes used by method slotAccept
        # *Cause query_info is mutable it is passed by reference and the caller
        # still can access it once the dialog has been closed.*
        # If the dialog is cancelled these initial values will be returned to
        # the caller. If the dialog is accepted then these values will be
        # updated (in the slotAccept method) and returned to the caller
        self.query_info = query_info
        self.query_info['condition'] = ''
        self.query_info['rows_range'] = ()
        self.query_info['ft_name'] = ''
        self.query_info['indices_field_name'] = ''

        # Main widgets
        # Global Options section
        global_opt_gb = qt.QGroupBox(self.__tr('Global options',
            'A groupbox title'), self)
        dlg_layout.addWidget(global_opt_gb)
        # Table name text box
        self.name_le = qt.QLineEdit('FilteredTable_%s' % counter, global_opt_gb)
        qt.QWhatsThis.add(self.name_le, self.__tr(
            """<qt>
            The name of the table where the query results will be added.
            </qt>""",
            'A help text for the Query dialog'))
        # Indices field name widgets
        self.indices_checkbox = qt.QCheckBox(global_opt_gb)
        self.indices_column = qt.QLineEdit('Orig_idx', global_opt_gb)
        qt.QWhatsThis.add(self.indices_column, self.__tr(
            """<qt>
            The name of the column where the indices of the selected rows
            will be added.
            </qt>""",
            'A help text for the Query dialog')
            )
        # Condition section
        condition_gb = qt.QGroupBox(self.__tr('Query condition',
            'A groupbox title'), self)
        dlg_layout.addWidget(condition_gb)
        self.query_le = qt.QLineEdit(condition_gb)
        qt.QWhatsThis.add(self.query_le, self.__tr(\
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
        self.operators_cb = qt.QComboBox(condition_gb)
        qt.QWhatsThis.add(self.operators_cb, self.__tr(
            """<qt>
            The operators that can be used in a given condition. Operators
            can be logical, comparison and arithmetic.<br>Not all operators
            are available for every data type.
            </qt>""",
            'A help text for the Query dialog')
            )
        self.functions_cb = qt.QComboBox(condition_gb)
        qt.QWhatsThis.add(self.functions_cb, self.__tr(
            """<qt>
            The set of functions that can appear in a condition.
            It includes functions for doing selections, trigonometric
            functions and functions on complex numbers. For ease
            of use arguments are automatically included when a
            function is inserted. The arguments meaning is:
            <ul><li>N: number</li><li>B: boolean</li>
            <li>F: float</li><li>C: complex</li></ul>
            </qt>""",
            'A help text for the Query dialog')
            )
        self.columns_cb = qt.QComboBox(False, condition_gb)
        qt.QWhatsThis.add(self.columns_cb, self.__tr(
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
            qt.QGroupBox(self.__tr('Range of rows', 'A groupbox title'), self)
        qt.QWhatsThis.add(rows_range_gb, self.__tr(
            """The range of rows included in the query.""",
            'A help text for the Query dialog')
            )
        dlg_layout.addWidget(rows_range_gb)
        self.rstart = qt.QLineEdit('', rows_range_gb)
        self.rstop = qt.QLineEdit('', rows_range_gb)
        self.rstep = qt.QLineEdit('', rows_range_gb)
        validator = qt.QRegExpValidator(qt.QRegExp("\\d*"), self)
        self.rstart.setValidator(validator)
        self.rstop.setValidator(validator)
        self.rstep.setValidator(validator)
        # The OK and Cancel buttons section
        buttons_layout = qt.QHBoxLayout(dlg_layout, 5)
        self.ok_button = \
            qt.QPushButton(self.__tr('&OK', 'A button label'), self)
        self.cancel_button = \
            qt.QPushButton(self.__tr('&Cancel', 'A button label'), self)
        self.help_button = \
            qt.QPushButton(self.__tr("&What's This", 'A button label'), self)

        # Add components to dialog
        self.makeSectionOne(global_opt_gb)
        self.makeSectionTwo(condition_gb, info['valid_fields'])
        self.makeSectionThree(rows_range_gb, info['nrows'])
        self.makeSectionFour(buttons_layout)

        # Use the values of the last query done on this table (if any)
        if initial_query != '':
            self.query_le.setText(initial_query)

        # Connect signals to slots
        self.connect(self.help_button, qt.SIGNAL('clicked()'),
            slotEnterHelpMode)
        self.connect(self.indices_checkbox, qt.SIGNAL('toggled(bool)'),
            self.slotEnableIndicesColumn)
        self.connect(self.name_le, qt.SIGNAL('textChanged(const QString &)'),
            self.slotUpdateOKState)
        self.connect(self.indices_column,
            qt.SIGNAL('textChanged(const QString &)'), self.slotUpdateOKState)
        self.connect(self.query_le, qt.SIGNAL('textChanged(const QString &)'),
            self.slotUpdateOKState)
        self.connect(self.rstart, qt.SIGNAL('textChanged(const QString &)'),
            self.slotUpdateOKState)
        self.connect(self.rstop, qt.SIGNAL('textChanged(const QString &)'),
            self.slotUpdateOKState)
        self.connect(self.columns_cb, qt.SIGNAL('activated(const QString &)'),
            self.slotInsertField)
        self.connect(self.operators_cb, qt.SIGNAL('activated(const QString &)'),
            self.slotInsertOperator)
        self.connect(self.functions_cb, qt.SIGNAL('activated(const QString &)'),
            self.slotInsertFunction)
        self.connect(self.ok_button, qt.SIGNAL('clicked()'), self.slotAccept)
        self.connect(self.cancel_button, qt.SIGNAL('clicked()'),
            qt.SLOT('reject()'))
        # Ensure that if the condition line edit is initialised with an
        # initial condition then the OK button will be enabled
        self.name_le.emit(qt.SIGNAL('textChanged(const QString &)'),
            (self.name_le.text(), ))


    def __tr(self,  source, comment=None):
        """Translate method."""
        return qt.qApp.translate('QueryDlg', source, comment).latin1()


    def makeSectionOne(self, global_opt_gb):
        """
        Make the Global Options section.

        :Parameter global_opt_gb: the Global Options groupbox
        """

        global_opt_gb.setOrientation(qt.Qt.Vertical)
        global_opt_gb.setInsideMargin(10)
##        global_opt_gb.setInsideSpacing(6) # Doesn't work, PyQt bug??
        global_opt_gb.layout().setSpacing(6)

        # The table name
        name_layout = qt.QHBoxLayout(global_opt_gb.layout(), 5)
        name_layout.addWidget(qt.QLabel(self.__tr('Name:', 'A textbox label'),
            global_opt_gb))
        name_layout.addWidget(self.name_le)

        global_opt_gb.layout().addSpacing(6)

        # The column with original indices
        indices_layout = qt.QHBoxLayout(global_opt_gb.layout(), 5)
        self.indices_checkbox.setOn(0)
        indices_layout.addWidget(self.indices_checkbox)
        indices_layout.addWidget(qt.QLabel(\
            self.__tr('Original indices into column:',
            'A label in the Query-->New filter dialog'), global_opt_gb))
        self.indices_column.setEnabled(0)
        indices_layout.addWidget(self.indices_column)


    def makeSectionTwo(self, condition_gb, valid_fields):
        """
        Make the Condition section.

        :Parameters:

        - `criteria_gb`: the Criteria Selection groupbox
        - `valid_fields`: the set of searchable field names
        """

        condition_gb_layout = qt.QVBoxLayout(condition_gb, 10, 6)

        # Give room between the groupbox title and the first label
        spacer = \
            qt.QSpacerItem(5, 10,qt.QSizePolicy.Fixed, qt.QSizePolicy.Fixed)
        condition_gb_layout.addItem(spacer)

        # Add the query line editor to the groupbox layout
        condition_gb_layout.addWidget(self.query_le)
        # Add a horizontal layout to the groupbox layout. This new
        # layout contain the section combos
        combos_layout = qt.QHBoxLayout()
        condition_gb_layout.addLayout(combos_layout)
        combos_layout.addStretch(1)
        combos_layout.addWidget(self.columns_cb)
        combos_layout.addStretch(1)
        combos_layout.addWidget(self.operators_cb)
        combos_layout.addStretch(1)
        combos_layout.addWidget(self.functions_cb)
        combos_layout.addStretch(1)

        # Fill the combos
        operators = ['&', '|', '~', '<', '<=', '==', '!=', '>', '>=', '+',
            '-', '*', '/', '**', '%']
        functions = ['where', 'sin', 'cos', 'tan', 'arcsin', 'arccos',
            'arctan', 'arctan2', 'sinh', 'cosh', 'tanh', 'sqrt', 'real',
            'imag', 'complex']
        for item in operators:
            self.operators_cb.insertItem(item)
        for item in functions:
            self.functions_cb.insertItem(item)
        sorted_fields = [field for field in valid_fields]
        sorted_fields.sort()
        for field in sorted_fields:
            self.columns_cb.insertItem(field)


    def makeSectionThree(self, rows_range_gb, nrows):
        """
        Make the Range Selectors section.

        :Parameters:

        - `rows_range_gb`: the Rows Range groupbox
        - `nrows`: the number of rows of the table being filtered
        """

        range_layout = qt.QGridLayout(rows_range_gb, 4, 3, 11, 6)
        range_layout.setColStretch(2, 1)

        # Give room between the groupbox title and the first label
        spacer = \
            qt.QSpacerItem(30, 30,qt.QSizePolicy.Fixed, qt.QSizePolicy.Fixed)
        range_layout.addItem(spacer, 0, 0)

        start_label = qt.QLabel(self.__tr('Start:', 'A range selector label'),
            rows_range_gb)
        range_layout.addWidget(start_label, 1, 0)
        self.rstart.setText('1')
        range_layout.addWidget(self.rstart, 1, 1)

        stop_label = qt.QLabel(self.__tr('Stop:', 'A range selector label'),
            rows_range_gb)
        range_layout.addWidget(stop_label, 2, 0)
        self.rstop.setText(str(nrows))
        range_layout.addWidget(self.rstop, 2, 1)

        step_label = qt.QLabel(self.__tr('Step:', 'A range selector label'),
            rows_range_gb)
        range_layout.addWidget(step_label, 3, 0)
        self.rstep.setText('1')
        range_layout.addWidget(self.rstep, 3, 1)


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
        self.query_le.insert(' %s ' % operator)


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
        self.query_le.insert(field_id.latin1().split(' ')[0])


    def slotInsertFunction(self, text):
        """
        Update  the contents of the query line editor.

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
            'sqrt': 'sqrt(F|C)',
            'real': 'real(C)',
            'imag': 'imag(C)',
            'complex': 'complex(F, F)'
            }
        self.query_le.insert(name2call[text.latin1()])


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
        ft_name = self.name_le.text().latin1()
        if not ft_name:
            status_ok = False
        elif ft_name in self.used_names:
            status_ok = False
            print self.__tr("""The chosen name is already in use. Please,"""
                """ choose another one.""", 'A logger info message')

        # Check the indices column name
        indices_colname = self.indices_column.text().latin1()
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
        condition = self.query_le.text().latin1()
        if condition.isspace() or (condition in [None, '']):
            status_ok = False

        # Check the range values
        start_str = self.rstart.text().latin1()
        stop_str = self.rstop.text().latin1()
        if not (start_str and stop_str):
          status_ok = False
        else:
          start = numpy.array(start_str).astype(numpy.int64)
          stop = numpy.array(stop_str).astype(numpy.int64)
          if stop > self.num_rows:
              status_ok = False
          elif start > stop:
              status_ok = False
          elif start < 1:
              status_ok = False

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
        condition = self.query_le.text().latin1()
        # Blanks at the begining of condition raise a SyntaxError
        condition = condition.strip()
        if not self.checkConditionSyntax(condition):
            return

        self.query_info['condition'] = condition

        # Get the table name and the name of the column with indices (if any)
        self.query_info['ft_name'] = self.name_le.text().latin1()
        if self.indices_column.isEnabled():
            self.query_info['indices_field_name'] = \
                self.indices_column.text().latin1()

        # Get the range and convert it into a Python range
        self.query_info['rows_range'] = (
           numpy.array(self.rstart.text().latin1()).astype(numpy.int64) - 1,
           numpy.array(self.rstop.text().latin1()).astype(numpy.int64),
           numpy.array(self.rstep.text().latin1()).astype(numpy.int64))

        # Exit
        self.accept()


