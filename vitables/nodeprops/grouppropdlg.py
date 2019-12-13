#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2019 Vicent Mas. All rights reserved
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
This module displays in a dialog tables.Group information collected by the
:mod:`vitables.nodeprops.nodeinfo` module.

Users' attributes can be edited if the database has been opened in read-write
mode. Otherwise all shown information is read-only.
"""

__docformat__ = 'restructuredtext'

from qtpy import QtGui
from qtpy import QtWidgets

from vitables.nodeprops import attrpropdlg
from vitables.nodeprops import groupproppage

translate = QtWidgets.QApplication.translate


class GroupPropDlg(attrpropdlg.AttrPropDlg):
    """
    Group properties dialog.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    This class displays a tabbed dialog that shows some properties of
    the selected node. First tab, General, shows general properties like
    name, path, type etc. The second and third tabs show the system and
    user attributes in a tabular way.

    Beware that data types shown in the General page are `PyTables` data
    types so we can deal with `enum`, `time64` and `pseudoatoms` (none of them
    are supported by ``numpy``).
    However data types shown in the System and User attributes pages are
    ``numpy`` data types because `PyTables` attributes are stored as ``numpy``
    arrays.

    :Parameter info: a :meth:`vitables.nodeprops.nodeinfo.NodeInfo` instance
      describing a given node
    """

    def __init__(self, info):
        """Setup the Properties dialog."""

        super(GroupPropDlg, self).__init__(info)

        general_page = groupproppage.GroupPropPage(info)
        self.tabw.insertTab(0, general_page, 'General')
        self.tabw.setCurrentIndex(0)

        if info.node_type == 'root group':
            self.setWindowTitle(translate('GroupPropDlg', 'File properties',
            'Dlg caption'))
        else:
            self.setWindowTitle(translate('GroupPropDlg', 'Group properties',
                'Dlg caption'))
            general_page.regularGroupPage()

        self.show()

