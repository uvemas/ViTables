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
#       $Id: groupDoc.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the GroupDoc class.

Classes:

* GroupDoc(NodeDoc)

Methods:

* __init__(self, dbdoc, nodepath)
* getNodeName(self)
* nodeTitle(self)
* getNodePathName(self)
* getFileObject(self)
* getGroupNodes(self)
* getLeafNodes(self)
* getRootGroupInfo(self)
* getNodeInfo(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import os

from vitables.nodes.nodeDoc import NodeDoc

class GroupDoc(NodeDoc):
    """
    A data structure that defines a tables.Group.

    This class represents a model and is controlled by the leaves
    manager. It exposes methods to get node metadata and data (via
    buffer).
    """


    def __init__(self, dbdoc, nodepath):
        """
        Creates a document that represents a node (group or leaf).

        :Parameters:

        - `dbdoc`: the database where node lives
        - `nodePath`: the full path of node in the database object tree
        """
        NodeDoc.__init__(self, dbdoc, nodepath)
        self.format = dbdoc.getFileFormat()


    def getNodeName(self):
        """:Returns: the node name in `Python` namespace"""
        return self.node._v_name


    def nodeTitle(self):
        """
        The node title.

        The `Python` attribute title is mapped to the system attribute
        `TITLE`. If it doesn't exist (as it can happen in generic `HDF5`
        arrays) the title attribute is empty.

        :Returns: the title attribute
        """
        return self.node._v_title


    def getNodePathName(self):
        """
        :Returns: a string representation of the node location in the
        tree
        """
        return self.node._v_pathname


    def getFileObject(self):
        """:Returns: a pointer to the `File` object associated to this node"""
        return self.node._v_file


    def getGroupNodes(self):
        """:Returns: the dictionary of groups hanging from this node"""
        return self.node._v_groups


    def getLeafNodes(self):
        """:Returns: the dictionary of leaves hanging from this node"""
        return self.node._v_leaves


    #
    # These methods are used mainly by the leaves manager in order to display
    # dialogs of properties
    #


    def getRootGroupInfo(self):
        """
        Get info about the root node.

        The following info is returned: format, filename, filepath and
        mode.

        :Returns: a tuple with information about the root node
        """

        # File size
        bytes = os.path.getsize(self.filepath) *1.0
        kbytes = bytes/1024
        mbytes = kbytes/1024
        gbytes = mbytes/1024
        tbytes = gbytes/1024
        if kbytes < 1:
            size = '%d bytes' % bytes
        elif mbytes < 1:
            size = '%.0f KB' % (kbytes)
        elif gbytes < 1:
            size = '%.0f MB' % (mbytes)
        elif tbytes < 1:
            size = '%.0f GB' % (gbytes)
        else:
            size = '%.0f TB' % (tbytes)

        node_type = '%s, size=%s' % (self.format, size)
        mode = self.dbdoc.getFileMode()
        if mode == 'r':
            access = 'read-only'
        elif mode == 'w':
            access = 'read-write'
        else:
            access = 'append'

        # Return the tuple (node_type, filename, filepath, mode)
        return (node_type, os.path.basename(self.filepath), self.filepath,
            access)


    def getNodeInfo(self):
        """
        Get info about the node when it is a Group instance.

        Returned info is obtained from `tables.Group` instance
        attributes ``_v_file``, ``_v_pathname``, ``_v_name``,
        ``_v_groups``,  ``_v_leaves`` and ``_v_attrs``.
        The following info is returned: type, name, path, members,
        groups, leaves, attribute set instance, system attributes and
        user attributes.

        :Returns: a dictionary with information about the group
        """

        info = {}
        if self.nodepath == '/':
            # The node is the root group --> inspects the file
            info['type'], info['name'], info['path'], info['mode'] = self.getRootGroupInfo()
        else:
            # The node is a normal group
            info['type'] = 'Group'
            # Group name
            info['name'] = self.getNodeName()
            # Group path
            info['path'] = self.getNodePathName()

        # Dictionary of groups that hung directly from node
        info['groups'] = self.getGroupNodes()

        # Dictionary of leaves that hung directly from node
        info['leaves'] = self.getLeafNodes()

        # number of direct children
        info['members'] = str(len(info['groups']) + len(info['leaves']))

        # Attributes Set Instance and dictionaries
        info['asi'] = self.getASI()
        info['sysAttr'] = self.getNodeAttributes(kind='system')
        info['userAttr'] = self.getNodeAttributes(kind='user')

        return info
