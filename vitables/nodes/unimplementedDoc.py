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
#       $Id: unimplementedDoc.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the UnImplementedDoc class.

Classes:

* UnImplementedDoc(NodeDoc)

Methods:

* __init__(self, dbdoc, nodepath)
* __tr(self, source, comment=None)
* isReadable(self)
* getBuffer(self, *args)
* numCols(self, *args)
* getNodeInfo(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import qt

from vitables.nodes.nodeDoc import NodeDoc

class UnImplementedDoc(NodeDoc):
    """
    A data structure that defines a `tables.UnImplemented` instance.

    This class represents a model and is controlled by the leaves<br>
    manager. It exposes methods to get node metadata.
    """


    def __init__(self, dbdoc, nodepath):
        """
        Creates a document that represents a tables.Unimplemented instance.

        :Parameters:

        - `dbdoc`: the database where node lives
        - `nodepath`: the full path of node in the database object tree
        """

        NodeDoc.__init__(self, dbdoc, nodepath)


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('UnImplementedDoc', source, comment).latin1()


    def isReadable(self):
        """Check the dataset readability."""

        print  self.__tr("""\nError: UnImplemented datasets cannot be """\
            """read. As a consequence they cannot be copied, cut or moved """\
            """to a different location.""", 
            'A dataset readability error')
        return False


    def getBuffer(self, *args):
        """
        This method has no functionality. It is added just to make
        this class compliant with the rest of `NodeDoc` descendant
        classes. It also allows for a simpler code in the
        `VTApp.slotNodeOpen` method.
        """
        pass


    def numCols(self, *args):
        """
        This method has no functionality. It is added just to make
        this class compliant with the rest of `NodeDoc` descendant
        classes. It also allows for a simpler code in the <br>
        `VTApp.slotNodeOpen` method.
        """
        pass


    def getNodeInfo(self):
        """Get info about the node.

        :Returns: a literal string
        """
        return {'type': 'UnImplemented'}
