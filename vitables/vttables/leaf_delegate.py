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
A custom delegate for rendering selected cells.

As explained in the leaf_view module the current cell must be rendered
differently depending on the buffer being displayed. If the dataset row of the
current/selected cell is in the range of rows being displayed then the cell
should be rendered in the standard way. If it is not then it should always be
rendered unselected.
"""

__docformat__ = 'restructuredtext'

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

class LeafDelegate(QtWidgets.QStyledItemDelegate):
    """
    A delegate for rendering selected cells.

    :Parameter parent: the parent of this widget
    """


    def paint(self, painter, option, index):
        """Renders the delegate for the item specified by index.

        This method handles specially the result returned by the model data()
        method for the Qt.BackgroundRole role. Typically, if the cell being
        rendered is selected then the data() returned value is ignored and the
        value set by the desktop (KDE, Gnome...) is used. We need to change
        that behavior as explained in the module docstring.

        The following properties of the style option are used for customising
        the painting: state (which holds the state flags), rect (which holds
        the area that should be used for painting) and palette (which holds the
        palette that should be used when painting)

        :Parameters:

        - `painter`: the painter used for rendering
        - `option`: the style option used for rendering
        - `index`: the index of the rendered item
        """

        # option.state is an ORed combination of flags
        if (option.state & QtWidgets.QStyle.State_Selected):
            model = index.model()
            buffer_start = model.start
            cell = index.model().selected_cell
            if ((index == cell['index']) and \
                    (buffer_start != cell['buffer_start'])):
                painter.save()
                self.initStyleOption(option, index)
                background = option.palette.color(QtGui.QPalette.Base)
                foreground = option.palette.color(QtGui.QPalette.Text)
                painter.setBrush(QtGui.QBrush(background))
                painter.fillRect(option.rect, painter.brush())
                painter.translate(option.rect.x() + 3, option.rect.y())
                painter.setBrush(QtGui.QBrush(foreground))
                painter.drawText(
                    option.rect,
                    QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop,
                    model.data(index))
                painter.restore()
            else:
                QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
        else:
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
