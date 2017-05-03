# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'calculator.ui'
#
# Created: Tue Jul  8 11:45:41 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from qtpy import QtCore
from qtpy import QtWidgets

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class Ui_CalculatorDialog(object):
    def setupUi(self, CalculatorDialog):
        CalculatorDialog.setObjectName("CalculatorDialog")
        CalculatorDialog.resize(640, 480)
        self.gridLayout = QtWidgets.QGridLayout(CalculatorDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setObjectName("main_layout")
        self.save_layout = QtWidgets.QVBoxLayout()
        self.save_layout.setObjectName("save_layout")
        self.saved_label = QtWidgets.QLabel(CalculatorDialog)
        self.saved_label.setObjectName("saved_label")
        self.save_layout.addWidget(self.saved_label)
        self.saved_list =QtWidgets.QListWidget(CalculatorDialog)
        self.saved_list.setObjectName("saved_list")
        self.save_layout.addWidget(self.saved_list)
        self.list_buttons_layout = QtWidgets.QHBoxLayout()
        self.list_buttons_layout.setObjectName("list_buttons_layout")
        self.save_button = QtWidgets.QPushButton(CalculatorDialog)
        self.save_button.setObjectName("save_button")
        self.list_buttons_layout.addWidget(self.save_button)
        self.remove_button = QtWidgets.QPushButton(CalculatorDialog)
        self.remove_button.setObjectName("remove_button")
        self.list_buttons_layout.addWidget(self.remove_button)
        self.save_layout.addLayout(self.list_buttons_layout)
        self.main_layout.addLayout(self.save_layout)
        self.evaluation_layout = QtWidgets.QVBoxLayout()
        self.evaluation_layout.setObjectName("evaluation_layout")
        self.statements_label = QtWidgets.QLabel(CalculatorDialog)
        self.statements_label.setObjectName("statements_label")
        self.evaluation_layout.addWidget(self.statements_label)
        self.statements_edit = QtWidgets.QTextEdit(CalculatorDialog)
        self.statements_edit.setObjectName("statements_edit")
        self.evaluation_layout.addWidget(self.statements_edit)
        self.expression_label = QtWidgets.QLabel(CalculatorDialog)
        self.expression_label.setObjectName("expression_label")
        self.evaluation_layout.addWidget(self.expression_label)
        self.expression_edit = QtWidgets.QTextEdit(CalculatorDialog)
        self.expression_edit.setObjectName("expression_edit")
        self.evaluation_layout.addWidget(self.expression_edit)
        self.result_label = QtWidgets.QLabel(CalculatorDialog)
        self.result_label.setObjectName("result_label")
        self.evaluation_layout.addWidget(self.result_label)
        self.result_edit = QtWidgets.QLineEdit(CalculatorDialog)
        self.result_edit.setObjectName("result_edit")
        self.evaluation_layout.addWidget(self.result_edit)
        self.main_layout.addLayout(self.evaluation_layout)
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 3)
        self.gridLayout.addLayout(self.main_layout, 0, 0, 1, 1)
        self.buttons = QtWidgets.QDialogButtonBox(CalculatorDialog)
        self.buttons.setStandardButtons(QtWidgets.QDialogButtonBox.Apply|QtWidgets.QDialogButtonBox.Close)
        self.buttons.setObjectName("buttons")
        self.gridLayout.addWidget(self.buttons, 1, 0, 1, 1)

        self.retranslateUi(CalculatorDialog)
        QtCore.QMetaObject.connectSlotsByName(CalculatorDialog)

    def retranslateUi(self, CalculatorDialog):
        CalculatorDialog.setWindowTitle(_translate("CalculatorDialog", "Evaluate expression", None))
        self.saved_label.setText(_translate("CalculatorDialog", "Saved expressions:", None))
        self.saved_list.setToolTip(_translate("CalculatorDialog", "<html><head/><body><p>Saved expressions.</p></body></html>", None))
        self.save_button.setToolTip(_translate("CalculatorDialog", "<html><head/><body><p>Store expression for future use.</p></body></html>", None))
        self.save_button.setText(_translate("CalculatorDialog", "Save", None))
        self.remove_button.setToolTip(_translate("CalculatorDialog", "<html><head/><body><p>Remove the selected expression from the saved expressions list.</p></body></html>", None))
        self.remove_button.setText(_translate("CalculatorDialog", "Remove", None))
        self.statements_label.setText(_translate("CalculatorDialog", "Statements:", None))
        self.statements_edit.setToolTip(_translate("CalculatorDialog", "<html><head/><body>\n"
"<p>Set of python statements that will be executed before the expression is evaluated. This can be used to import additional modules or do preliminary calculations to simplify the expression.</p>\n"
"</body></html>", None))
        self.expression_label.setText(_translate("CalculatorDialog", "Expression:", None))
        self.expression_edit.setToolTip(_translate("CalculatorDialog", "<html><head/><body>\n"
"<p>The results of the expression will be  saved in the result table. This field must contain a valid expression that returns a pytables array, list or scalar.</p>\n"
"<p>The expression can contain references to open data nodes. A reference can either be absolute and start from a file name or relative to the current group. Data refenrence is a string which is build by joining group names that lead to the data by dots. For example: &quot;filename.h5.some_group.sub_group.mydata&quot;. If &quot;sub_group&quot; is the current group then the string &quot;mydata&quot; can  be used as reference.</p>\n"
"</body></html>", None))
        self.result_label.setText(_translate("CalculatorDialog", "Result table:", None))
        self.result_edit.setToolTip(_translate("CalculatorDialog", "<html><head/><body>\n"
"<p>Reference to the destination for the expression result. Data refenrence is a string which is build by joining group names that lead to the data by dots. For example: &quot;filename.h5.some_group.sub_group.myresult&quot;. If &quot;sub_group&quot; is the current group then the string &quot;myresult&quot; can  be used as reference.</p>\n"
"<p>The result table must not exitst.</p>\n"
"</body></html>", None))

