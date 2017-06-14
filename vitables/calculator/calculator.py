"""This module provides calculator functionality."""

# pylint: disable=W0212

import logging
import os
import re
from vitables.calculator.calculator_dlg import Ui_CalculatorDialog

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
import tables

import numpy as np
import vitables.calculator.evaluator as vtce
import vitables.utils as vtu


translate = QtCore.QCoreApplication.translate

log = logging.getLogger(__name__)


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
        answer = QtWidgets.QMessageBox.question(
            gui, translate('Calculator', 'Relative references are disabled'),
            question, buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if answer != QtWidgets.QMessageBox.Yes:
            return
    dialog = CalculatorDialog()
    dialog.exec_()


# Marker used as prefix to distinguish identifiers from functions.
IDENTIFIER_MARKER = '$'

# Regular expression used to find identifiers in an evaluation formula.
IDENTIFIER_RE = r'\$[\w.]+'


def extract_identifiers(expression):
    """Return a set of identifiers that appear in the expression."""
    return set(re.findall(IDENTIFIER_RE, expression))


def get_current_group():
    """Return selected pytables group.

    If zero or more then one items are selected then None is
    returned. If a group or file is selected then return it. If a
    pytables leaf is selected then return group that contains the
    leaf.

    """
    selected_nodes = vtu.getSelectedNodes()
    if len(selected_nodes) != 1:
        return None
    node = selected_nodes[0]
    if not isinstance(node, tables.Leaf):
        return node
    return node._v_parent


def create_group(group, path):
    """Given ancestor group and a path create a group."""
    if not path:
        return group
    node_name = path[0]
    rest_of_path = path[1:]
    if node_name in group._v_groups:
        return create_group(group._v_groups[node_name], rest_of_path)
    if node_name in group._v_children:  # child but not a group
        return None
    node_group = group._v_file.create_group(group, node_name)
    return create_group(node_group, rest_of_path)


def find_identifier_root(model, identifier):
    """Find the identifier root group in the model.

    Identifier is a string, root group is found by matching item name
    to identifier beggining. The second return argument contains path
    to to identifier node relative to root.

    """
    root_index = QtCore.QModelIndex()
    for row in range(model.rowCount(root_index)):
        index = model.index(row, 0, root_index)
        name = model.data(index, QtCore.Qt.DisplayRole)
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


class CalculatorDialog(QtWidgets.QDialog, Ui_CalculatorDialog):
    def __init__(self, parent=None):
        super(CalculatorDialog, self).__init__(parent)
        self.setupUi(self)
        self._name_expression_dict = {}
        self._settings = QtCore.QSettings()
        self._settings.beginGroup('Calculator')
        self._restore_expressions()

    def on_buttons_rejected(self):
        """Slot for cancel button, save expressions on exit."""
        self._store_expressions()
        self.reject()

    def on_buttons_clicked(self, button):
        """Slot for apply button, run and store saved expressions."""
        button_id = self.buttons.standardButton(button)
        if button_id == QtWidgets.QDialogButtonBox.Apply:
            if self._execute_expression():
                self._store_expressions()
                self.accept()

    @QtCore.Slot()
    def on_save_button_clicked(self):
        """Store expression for future use.

        Ask user for expression name. If provided name is new add it
        to saved expressions list widget. Store in/update name expression
        dictionary.

        """
        current_item = self.saved_list.currentItem()
        if current_item is None:
            # Either the list is empty or nothing is selected.
            current_name = ""
        else:
            current_name = current_item.text()
        name, is_accepted = QtWidgets.QInputDialog.getText(
            self, translate('Calculator', 'Save expression as'),
            translate('Calculator', 'Name:'), text=current_name)
        if not is_accepted:
            return
        if name not in self._name_expression_dict:
            self.saved_list.addItem(name)
        self._name_expression_dict[name] = (self.statements_edit.toPlainText(),
                                            self.expression_edit.toPlainText(),
                                            self.result_edit.text())

    @QtCore.Slot()
    def on_remove_button_clicked(self):
        """Remove stored expression.

        Delete selected row from saved widget and name expression
        dictionary.

        """
        current_row = self.saved_list.currentRow()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(
                self, translate('Calculator', 'Nothing selected'),
                translate('Calculator', 'No saved expression selected '
                          'to be removed.'))
            return
        removed_item = self.saved_list.takeItem(
            self.saved_list.currentRow())
        del self._name_expression_dict[removed_item.text()]

    def on_saved_list_itemSelectionChanged(self):
        """Update expression and result fields from selected item.

        Find first selected widget name, find name in expression
        dictionary and update expression and result widgets.

        """
        selected_indexes = self.saved_list.selectedIndexes()
        if len(selected_indexes) == 0:
            # KFP 2015-08-04: There is a race condition when removing a
            # stored expression.  Both this method and
            # ``on_remove_button_clicked`` are called very close to the
            # same time meaning ``self.saved_list.count()`` can show the
            # wrong value.
            return
        selected_index = selected_indexes[0]
        name = self.saved_list.itemFromIndex(selected_index).text()
        statements, expression, destination = self._name_expression_dict[name]
        self.statements_edit.setText(
            statements if statements is not None else ''
        )
        self.expression_edit.setText(
            expression if expression is not None else ''
        )
        self.result_edit.setText(
            destination if destination is not None else ''
        )

    def _store_expressions(self):
        """Store expressions in configuration.

        Save name expression dictionary in 'expression' part of
        configuration.

        """
        self._settings.beginWriteArray('expressions')
        for index, (name, (statements, expression, destination)) in enumerate(
                self._name_expression_dict.items()):
            self._settings.setArrayIndex(index)
            self._settings.setValue('name', name)
            self._settings.setValue('statements', statements)
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
            statements = self._settings.value('statements')
            expression = self._settings.value('expression')
            destination = self._settings.value('destination')
            self._name_expression_dict[name] = (statements, expression,
                                                destination)
            self.saved_list.addItem(name)
        self._settings.endArray()

    def _all_identifiers_found(self, identifiers, identifier_node_dict):
        """Return false if identifier is not found or references a group."""
        for identifier in identifiers:
            if identifier not in identifier_node_dict:
                QtWidgets.QMessageBox.critical(
                    self, translate('Calculator', 'Node not found'),
                    translate('Calculator',
                              'Node "{0}" not found'.format(identifier)))
                return False
            if not isinstance(identifier_node_dict[identifier], tables.Leaf):
                QtWidgets.QMessageBox.critical(
                    self, translate('Calculator', 'Node type'),
                    translate('Calculator',
                              'Node "{0}" does not contain data. '
                              'It is probably a group.'.format(identifier)))
                return False
        return True

    def _create_eval_globals_and_epsression(self, expression,
                                            identifier_node_dict):
        """Transform identifiers into valid python names, update expression."""
        eval_globals = {}
        for index, (identifier, node) in enumerate(
                identifier_node_dict.items()):
            variable_name = (identifier.replace('.', '_')
                             + '_calculator_index_' + str(index))
            expression = expression.replace(
                IDENTIFIER_MARKER + identifier, variable_name)
            eval_globals[variable_name] = node
        return eval_globals, expression

    def _get_result_group_and_name(self):
        """Find or create a group for result based on provided name."""
        result_identifier = self.result_edit.text()
        if not result_identifier:
            QtWidgets.QMessageBox.critical(
                self, translate('Calculator', 'Result name'),
                translate('Calculator',
                          'The location to store results is not specified'))
            return None
        model = vtu.getModel()
        result_ancestor, relative_path = find_identifier_root(
            model, result_identifier)
        if result_ancestor is None:
            result_ancestor = get_current_group()
            relative_path = result_identifier
        relative_path = relative_path.split('.')
        result_group = find_node(result_ancestor, relative_path[:-1])
        if result_group is None:
            answer = QtWidgets.QMessageBox.question(
                self, translate('Calculator', 'Create group'),
                translate('Calculator', 'There is no group "{group}" in '
                          '"{ancestor}". File "{filename}". Create it?'.format(
                              group='/'.join(relative_path[:-1]),
                              ancestor=result_ancestor._v_pathname,
                              filename=result_ancestor._v_file.filename)),
                buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if answer != QtWidgets.QMessageBox.Yes:
                return None
            result_group = create_group(result_ancestor, relative_path[:-1])
            if result_group is None:
                QtWidgets.QMessageBox.critical(
                    self, translate('Calculator', 'Result name'),
                    translate('Calculator',
                              'Failed to create group "{group}" inside '
                              '{ancestor} to hold results. File "{filename}".'
                              ''.format(
                                  group='/'.join(relative_path[:-1]),
                                  ancestor=result_ancestor._v_pathname,
                                  filename=result_ancestor._v_file.filename)))
                return None
        result_name = relative_path[-1]
        if result_name in result_group._v_children:
            QtWidgets.QMessageBox.critical(
                self, translate('Calculator', 'Result name'),
                translate('Calculator',
                          'Node "{node}" already exists in group "{group}". '
                          'File "{filename}". Choose another place to store '
                          'results.'.format(
                              node=result_name,
                              group=result_group._v_pathname,
                              filename=result_group._v_file.filename)))
            return None, None
        return result_group, result_name

    def _execute_expression(self):
        """Execute expression and store results.

        Check existence of all tables used in the expression and
        result.

        """
        statements = self.statements_edit.toPlainText()
        expression = self.expression_edit.toPlainText()
        identifier_strings = extract_identifiers(expression)
        identifiers = [i[1:] for i in identifier_strings]
        current_group = get_current_group()
        identifier_node_dict = build_identifier_node_dict(identifiers,
                                                          current_group)
        if not self._all_identifiers_found(identifiers, identifier_node_dict):
            return False
        eval_globals, expression = self._create_eval_globals_and_epsression(
            expression, identifier_node_dict)
        results = self._get_result_group_and_name()
        if results is None:
            return False
        result_group, result_name = results
        try:
            result = vtce.evaluate(statements, expression, eval_globals)
        except Exception as e:
            log.error(str(e))
            QtWidgets.QMessageBox.critical(
                self, translate('Calculator', 'Evaluation error'),
                translate('Calculator', 'An exception was raised during '
                          'evaluation, see log for details.'))
            return False
        if not isinstance(result, np.ndarray):
            if isinstance(result, (list, tuple)):
                result = np.array(result)
            else:
                result = np.array([result])
        try:
            result_group._v_file.create_array(
                result_group, result_name, obj=result,
                title='Expression: ' + self.expression_edit.toPlainText())
        except Exception as e:
            log.error(str(e))
            QtWidgets.QMessageBox.critical(
                self, translate('Calculator', 'Result save error'),
                translate('Calculator', 'An exception was raised while '
                          'trying to store results, see log for details.'))
            return False
        vtu.getModel().updateTreeFromData()
        return True
