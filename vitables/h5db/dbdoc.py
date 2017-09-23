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
This module provides a thin wrapper to the `tables.File` class.

The module provides methods for opening and closing PyTables databases. It also
contains methods for editing nodes (but not data stored in nodes).

"""

import logging
import os
import uuid
import vitables.utils

from qtpy import QtCore
from qtpy import QtWidgets
import tables

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate

log = logging.getLogger(__name__)


class DBDoc(QtCore.QObject):
    """
    A database contained in an hdf5/PyTables file.

    :Parameters:

    - `filePath`: full path of the DB
    - `mode`: indicate the open mode of the database file. It can be
      'r'ead-only or 'a'ppend
    - `is_tmp_dbdoc`: True if this object represents the temporary database
    """

    def __init__(self, filepath, mode, is_tmp_dbdoc=False):
        """
        Makes a data structure that defines a given database.

        A `DBDoc` instance is defined by the next attributes:

        - filepath
        - filename
        - mode
        - h5file, the File instance returned when filePath is opened
        """

        super(DBDoc, self).__init__()

        # The opening mode
        self.mode = mode

        # The full path of the database
        self.filepath = filepath

        # The filename of the database
        self.filename = os.path.basename(filepath)

        # The tables.File instance
        self.h5file = self.openH5File()

        # Hidden groups are used as an intermediate storage
        # in cut operations
        self.hidden_group = None

        if is_tmp_dbdoc:
            self.h5file.create_group('/', '_p_query_results',
                                     'Hide the result of queries')
            self.h5file.flush()

    def openH5File(self):
        """Open the file tied to this instance."""

        h5file = None
        # If read-write access is required then test file writability
        if self.mode != 'r' and os.path.isfile(self.filepath):
            if not os.access(self.filepath, os.W_OK):
                self.mode = 'r'
                log.warning(
                    translate('DBDoc',
                              """File access in read-write mode """
                              """is denied. It will be opened in read-only """
                              """mode.""", 'A logger error message'))

        try:
            h5file = tables.open_file(self.filepath, self.mode)
        except IOError as inst:
            log.error(translate('DBDoc', "{0}",
                                'A logger error message').format(inst))
        except:
            vitables.utils.formatExceptionInfo()
            log.error(
                translate('DBDoc',
                          "Please, if you think it is a bug, report it to "
                          "developers.", 'A logger error message'))

        return h5file

    def closeH5File(self):
        """Closes a tables.File instance."""

        try:
            self.h5file.close()
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()

    def getFileFormat(self):
        """
        The format of the database file.

        This is an accessor method intended to be used by external
        classes.

        :Returns: the format of the database file
        """

        file_format = None
        if self.h5file:
            if self.h5file._isPTFile:
                file_format = 'PyTables file'
            else:
                file_format = 'Generic HDF5 file'

        return file_format

    def get_node(self, where):
        """
        The node whose path is where.

        :Parameter where: the full path of the retrieved node
        """

        try:
            node = self.h5file.get_node(where)
            return node
        except tables.exceptions.NoSuchNodeError:
            log.error(
                translate('DBDoc',
                          """Cannot open node {0} in file {1} """,
                          'Error message').format(where, self.filepath))
            vitables.utils.formatExceptionInfo()
            return None

    def list_nodes(self):
        """:Returns: the recursive list of full nodepaths for the file"""
        return [node._v_pathname for node in self.h5file.walk_nodes('/')]

    #
    # Editing databases
    #

    def copy_file(self, dst_filepath):
        """
        Copy the contents of this file to another one.

        .. Note:: Given two open files in a ``ViTables`` session, overwriting
          one of them via ``File --> Save As...`` command may work or not. It
          depends on the operating system. On Unices it works because a process
          can delete or truncate a file open by a different process (unless
          file is blocked). On Windows it seems to work fine too.

        If the overwriting is not done via ``ViTables`` but in an interactive
        session it fails, due (probably) to `HDF5` memory protection.

        :Parameter dst_filepath: the full path of the destination file
        """

        try:
            self.h5file.copy_file(dst_filepath, overwrite=True)
        except tables.exceptions.HDF5ExtError:
            log.error(
                translate('DBDoc',
                          """Unable to save the file {0} as """
                          """{1}. Beware that only closed files can be """
                          """safely overwritten via Save As...""",
                          'A logger error message').format(self.filepath,
                                                           dst_filepath))
            vitables.utils.formatExceptionInfo()

    def createHiddenGroup(self):
        """
        Create a hidden group for storing cut nodes.
        """

        group_name = '_p_' + str(uuid.uuid4())
        self.hidden_group = '/' + group_name
        self.h5file.create_group('/', group_name, 'Hide cut nodes')
        self.h5file.flush()

