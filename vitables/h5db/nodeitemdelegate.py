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
Here is defined the NodeItemDelegate class.
"""

__docformat__ = 'restructuredtext'

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.utils

translate = QtWidgets.QApplication.translate

class NodeItemDelegate(QtWidgets.QItemDelegate):
    """
    A custom delegate for editing items of the tree of databases model.

    The delegate is used for editing the text of items of the tree of
    databases model, i.e., the item's DisplayRole. In other words, it is
    used to edit the name of the nodes in a database object tree.
    """

    def __init__(self, vtgui, parent=None):
        """
        Creates the custom delegate.
        """

        super(NodeItemDelegate, self).__init__(parent)
        self.current_name = None
        self.vtgui = vtgui


    def setEditorData(self, editor, index):
        """
        Edits the data of an item with a given index.

        This method is automatically called when an editor is created,
        i.e., when the user double click an item while the `Shift` key is
        pressed.

        :Parameters:

        - `editor`: the editor widget
        - `index`: the index of the item being edited
        """

        node_name = index.model().data(index, QtCore.Qt.DisplayRole)
        self.current_name = node_name
        editor.setText(node_name)


    def setModelData(self, editor, model, index):
        """
        Update the model with the just edited data.

        This method is called automatically when an editor is closed,
        i.e., when the user editing ends.

        :Parameters:

        - `editor`: the editor widget
        - `model`: the model whose data is being setup
        - `index`: the index of the item being edited
        """

        suggested_nodename = editor.text()

        node = model.nodeFromIndex(index)  # A GroupNode or a LeafNode instance
        parent = node.parent

        #
        # Check if the nodename is already in use
        #
        sibling = getattr(parent.node, '_v_children').keys()
        # Note that current nodename is not allowed as new nodename.
        # Embedding it in the pattern makes unnecessary to pass it to the
        # rename dialog via method argument and simplifies the code
        pattern = """(^{0}$)|""" \
            """(^[a-zA-Z_]+[0-9a-zA-Z_ ]*)""".format(self.current_name)
        info = [translate('NodeItemDelegate',
            'Renaming a node: name already in use',
            'A dialog caption'),
            translate('NodeItemDelegate',
                """Source file: {0}\nParent group: {1}\n\nThere is """
                """already a node named '{2}' in that parent group.\n""",
                'A dialog label').format\
                    (parent.filepath, parent.nodepath, suggested_nodename)]
        # Validate the nodename
        nodename, overwrite = vitables.utils.getFinalName(suggested_nodename,
            sibling, pattern, info)
        if nodename is None:
            editor.setText(self.current_name)
            return

        # Update the underlying data structure
        model.rename_node(index, nodename, overwrite)
        self.closeEditor.emit(editor, 0)

        # Update the application status bar
        self.vtgui.updateStatusBar()
