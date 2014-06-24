"""This module provides calculator functionality."""

import os

import PyQt4.QtGui as qtgui
from PyQt4 import uic

Ui_Calculator = uic.loadUiType(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'calculator.ui'))[0]


def run():
    dialog = CalculatorDialog()
    dialog.exec_()


class CalculatorDialog(qtgui.QDialog, Ui_Calculator):
    def __init__(self, parent=None):
        super(CalculatorDialog, self).__init__(parent)
        self.setupUi(self)
