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
#       $Id: vtTableItem.py 1083 2008-11-04 16:41:02Z vmas $
#
########################################################################

"""Here is defined the VTTableItem class.

Classes:

* VTTableItem(qttable.QTableItem)

Methods:

* __init__(self, table, ro, text='', p=None)
* alignment(self)
* createEditor(self)
* paint(self, p, cg, cr, s)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import qt
import qttable

class VTTableItem(qttable.QTableItem):

    def __init__(self, table, ro, text='', p=None):
        """
        A customised QTableItem.

        The ro argument is used to set the `EditType` value for the item.
        Only two values are used `QTableItem.OnTyping` and `QTableItem.Never`.

        :Parameters:

        - `table`: the parent `QTable` widget
        - `ro`: iindicates if the item is or not read-only
        - `text`: the item text
        - `p`: the item pixmap
        """

        if ro == True:
            qttable.QTableItem.__init__(self, table, qttable.QTableItem.Never)
        else:
            qttable.QTableItem.__init__(self, table, qttable.QTableItem.OnTyping)
        if text:
            self.setText(text)
        if p:
            self.setPixmap(p)


    def alignment(self):
        """Define the alignement of the `QTableItem`."""
        return  qt.Qt.AlignLeft | qt.Qt.AlignTop


    def createEditor(self):
        """
        Create a customised editor that highlight its contents.

        This method is **not** called via table.editCell(r, c) if
        table is in read-only mode.
        """

        if self.editType() == qttable.QTableItem.OnTyping:
            t = self.table()
            cell = (self.row(), self.col())
            le = qt.QLineEdit(self.text(), t.viewport())
            le.setFrame(0)
            le.setPaletteBackgroundColor(qt.QTextEdit().palette().active().base())
            le.selectAll()
            return le


    def paint(self, p, cg, cr, s):
        """
        Paint the content of an item.

        The tricky thing here is that the color group is passed by
        the parent table but we modify it for our convenience.

        :Parameters:

        - `p`: the painter
        - `cg`: the color group
        - `cr`: the cell rectangle
        - `s`: 
          if TRUE the item is painted in a way that indicates that it is
          highlighted
        """

        if self.editType() == qttable.QTableItem.Never:
            t=qttable.QTable()
            t.setReadOnly(1)
            bg = t.palette().active().background()
            cg.setColor(qt.QColorGroup.Base, bg)
        else:
            cg = qt.qApp.palette().active()
        qttable.QTableItem.paint(self, p, cg, cr, s)
