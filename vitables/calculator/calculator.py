"""This module provides calculator functionality."""

import os
import re

import PyQt4.QtGui as qtgui
import PyQt4.QtCore as qtcore
from PyQt4 import uic

import vitables.utils as vtu

translate = qtcore.QCoreApplication.translate

Ui_Calculator = uic.loadUiType(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'calculator.ui'))[0]


def run():
    dialog = CalculatorDialog()
    dialog.exec_()


# Regular expression used to find identifiers in an evaluation formula.
IDENTIFIER_RE = r'\$[\w.]+'


def extract_identifiers(expression):
    """Return a set of identifiers that appear in the expression."""
    return set(re.findall(IDENTIFIER_RE, expression))


class CalculatorDialog(qtgui.QDialog, Ui_Calculator):
    def __init__(self, parent=None):
        super(CalculatorDialog, self).__init__(parent)
        self.setupUi(self)
        self._name_expression_dict = {}
        self._settings = qtcore.QSettings()
        self._settings.beginGroup('Calculator')
        self._restore_expressions()

    def on_buttons_rejected(self):
        """Slot for cancel button, save expressions on exit."""
        self._store_expressions()
        self.reject()

    def on_buttons_clicked(self, button):
        """Slot for apply button, run and store saved expressions."""
        button_id = self.buttons.standardButton(button)
        if button_id == qtgui.QDialogButtonBox.Apply:
            self._execute_expression()
            self._store_expressions()
            self.accept()

    @qtcore.pyqtSlot()
    def on_save_button_clicked(self):
        """Store expression for future use.

        Ask user for expression name. If provided name is new add it
        to saved expressions list widget. Store in/update name expression
        dictionary.

        """
        name, is_accepted = qtgui.QInputDialog.getText(
            self, translate('Calculator', 'Save expression as'),
            translate('Calculator', 'Name:'))
        if not is_accepted:
            return
        if name not in self._name_expression_dict:
            self.saved_list.addItem(name)
        self._name_expression_dict[name] = (self.expression_edit.toPlainText(),
                                            self.result_edit.text())

    @qtcore.pyqtSlot()
    def on_remove_button_clicked(self):
        """Remove stored expression.

        Delete selected row from saved widget and name expression
        dictionary.

        """
        removed_item = self.saved_list.takeItem(self.saved_list.currentRow())
        del self._name_expression_dict[removed_item.text()]

    def on_saved_list_itemSelectionChanged(self):
        """Update expression and result fields from selected item.

        Find first selected widget name, find name in expression
        dictionary and update expression and result widgets.

        """
        selected_index = self.saved_list.selectedIndexes()[0]
        name = self.saved_list.itemFromIndex(selected_index).text()
        expression, destination = self._name_expression_dict[name]
        self.expression_edit.setText(expression)
        self.result_edit.setText(destination)

    def _store_expressions(self):
        """Store expressions in configuration.
        
        Save name expression dictionary in 'expression' part of
        configuration.

        """
        self._settings.beginWriteArray('expressions')
        for index, (name, (expression, destination)) in enumerate(
                self._name_expression_dict.items()):
            self._settings.setArrayIndex(index)
            self._settings.setValue('name', name)
            self._settings.setValue('expression', expression)
            self._settings.setValue('destination', destination)
        self._settings.endArray()

    def _restore_expressions(self):
        """Read stored expressions from settings and update list widget.

        Load name expression dictionary from 'expressions' part of
        configuration, update list widget.

        """
        expressions_count = self._settings.beginReadArray('expressions')
        for i in range(expressions_count):
            self._settings.setArrayIndex(i)
            name = self._settings.value('name')
            expression = self._settings.value('expression')
            destination = self._settings.value('destination')
            self._name_expression_dict[name] = (expression, destination)
            self.saved_list.addItem(name)
        self._settings.endArray()

    def _execute_expression(self):
        """Execute expression and store results.

        Check existence of all tables used in the expression and
        result.

        """
        expression = self.expression_edit.toPlainText()
        identifiers = extract_identifiers(expression)
        model = vtu.getModel()
        view = vtu.getView()
