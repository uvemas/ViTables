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
This module displays in a dialog the link information collected by the
:mod:`vitables.nodeprops.nodeinfo` module.
"""

import os.path

from qtpy import QtGui
from qtpy import QtWidgets

from qtpy.uic import loadUiType

import vitables.utils

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate
# This method of the PyQt5.uic module allows for dinamically loading user
# interfaces created by QtDesigner. See the PyQt5 Reference Guide for more
# info.
Ui_LinkPropDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__), 'link_prop_dlg.ui'))[0]


class LinkPropDlg(QtWidgets.QDialog, Ui_LinkPropDialog):
    """
    Link properties dialog.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    This class displays a simple dialog that shows some properties of
    the selected link: name, path, type and target.

    :Parameter info: a :meth:`vitables.nodeprops.nodeinfo.NodeInfo` instance
      describing a given node
    """

    def __init__(self, info):
        """Setup the Properties dialog."""

        vtapp = vitables.utils.getVTApp()
        super(LinkPropDlg, self).__init__(vtapp.gui)
        self.setupUi(self)

        self.setWindowTitle(translate('LinkPropDlg', 'Link properties',
                                      'Dlg caption'))

        # Customise the dialog's pages
        self.fillPage(info)
        self.resize(self.size().width(), self.minimumHeight())

        # Show the dialog
        self.show()

    def fillPage(self, info):
        """Fill the dialog with info regarding the given link.

        :Parameter info: a :meth:`vitables.nodeprops.nodeinfo.NodeInfo` instance
          describing a given node
        """

        self.nameLE.setText(info.nodename)
        self.pathLE.setText(info.nodepath)
        self.typeLE.setText(info.link_type)
        self.targetLE.setText(info.target)
