"""This module provides calculator functionality."""

import os
import re

import PyQt4.QtGui as qtgui
import PyQt4.QtCore as qtcore
from PyQt4 import uic

import tables

import vitables.utils as vtu

translate = qtcore.QCoreApplication.translate

Ui_Calculator = uic.loadUiType(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'calculator.ui'))[0]


def run():
    gui = vtu.getGui()
    selection_count = len(vtu.getView().selectedIndexes())
    question = ''
    if selection_count == 0:
        question = translate('Calculator', 'No group is selected. '
                             'Relative references are disabled. '
                             'Continue?')
    if selection_count > 1:
        question = translate('Calculator',
                             'Multiple groups are selected. '
                             'Relative references are disabled. '
                             'Continue?')
    if question:
        answer = qtgui.QMessageBox.question(
            gui, translate('Calculator', 'Relative references are disabled'),
            question, buttons=qtgui.QMessageBox.Yes | qtgui.QMessageBox.No)
        if answer != qtgui.QMessageBox.Yes:
            return
    dialog = CalculatorDialog()
    dialog.exec_()


# Regular expression used to find identifiers in an evaluation formula.
IDENTIFIER_RE = r'\$[\w.]+'


def extract_identifiers(expression):
    """Return a set of identifiers that appear in the expression."""
    return set(re.findall(IDENTIFIER_RE, expression))


def get_current_group():
    """Return current pytables group.

    If zero or more then one items are selected then None is
    returned. If a group or file is selected then return it. If a
    pytables leaf is selected then return group that contains the
    leaf.

    """
    selected_nodes = vtu.getSelectedLeafs()
    if len(selected_nodes) != 1:
        return None
    node = selected_nodes[0]
    if not isinstance(node, tables.Leaf):
        return node
    return node._v_parent


def find_identifier_root(model, identifier):
    """Find the identifier root group in the model.

    Identifier is a string, root group is found by matching item name
    to identifier beggining. The second return argument contains path
    to to identifier node relative to root.

    """
    root_index = qtcore.QModelIndex()
    for row in range(model.rowCount(root_index)):
        index = model.index(row, 0, root_index)
        name = model.data(index, qtcore.Qt.DisplayRole)
        if identifier.startswith(name):
            return (model.nodeFromIndex(index).node,
                    identifier[len(name) + 1:])
    return None, None


def find_node(start_node, path):
    """Given group and a list of node names return node referenced by path."""
    if not path or start_node is None:
        return start_node
    if not isinstance(start_node, tables.Group):
        return None
    if path[0] in start_node._v_children:
        return find_node(start_node._v_children[path[0]], path[1:])
    else:
        return None


def build_identifier_node_dict(identifiers, current_group):
    """Map identifiers to pytables nodes."""
    model = vtu.getModel()
    identifier_node_dict = {}
    for identifier in identifiers:
        identifier_ancestor, relative_path = find_identifier_root(model,
                                                                  identifier)
        if identifier_ancestor is None:
            identifier_ancestor = current_group
            relative_path = identifier
        identifier_node = find_node(identifier_ancestor,
                                    relative_path.split('.'))
        if identifier_node:
            identifier_node_dict[identifier] = identifier_node
    return identifier_node_dict


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
        identifier_strings = extract_identifiers(expression)
        identifiers = [i[1:] for i in identifier_strings]
        current_group = get_current_group()
        identifier_node_dict = build_identifier_node_dict(identifiers,
                                                          current_group)
        for identifier in identifiers:
            if identifier not in identifier_node_dict:
                qtgui.QMessageBox.critical(
                    self, translate('Calculator', 'Node not found'),
                    translate('Calculator',
                              'Node "{0}" not found'.format(identifier)))
                return
            if not isinstance(identifier_node_dict[identifier], tables.Leaf):
                qtgui.QMessageBox.critical(
                    self, translate('Calculator', 'Node type'),
                    translate('Calculator',
                              'Node "{0}" is not a leaf'.format(identifier)))
                return
        eval_globals = {}
        for index, (identifier, node) in enumerate(
                identifier_node_dict.items()):
            variable_name = identifier.replace('.', '_') \
                            + '_calculator_index_' + str(index)
            expression = expression.replace('$' + identifier, variable_name)
            eval_globals[variable_name] = node

