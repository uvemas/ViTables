#!/usr/bin/env python3

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

"""Test class for filenode nodes."""

import os.path

import pytest

import vitables.filenodeutils as fnutils
import vitables.vttables.filenodebuffer as fnbuffer


@pytest.mark.usefixtures('launcher', 'h5file')
class TestFilenode:
    """Test class for modules filenodutils and filenodebuffer."""

    @pytest.fixture()
    def fnode(self, h5file):
        return h5file.get_node('/filenode')

    def test_isFilenode(self, fnode, h5file):
        # Filenode node
        assert fnutils.isFilenode(fnode)

        # No filenode node
        node = h5file.get_node('/tables/Particles')
        assert not fnutils.isFilenode(node)

    def test_filenodeToFile(self, launcher, fnode):
        file = fnutils.filenodeToFile(fnode)
        assert os.path.isfile(file)

        with open(file, 'r') as f:
            lines = f.readlines()
        assert lines[-1] == 'This is the last line.\n'

        # We have to do this by hand because the VTApp.nodeOpen method is
        # not being called
        launcher.vtapp_object.filenodes_map[fnode] = file, len(lines)

    def test_filenodeTotalRows(self, fnode):
        assert fnutils.filenodeTotalRows(fnode) == 11

    def test_fnbTotalNRows(self, fnode):
        # The filenode buffer
        fnb = fnbuffer.FilenodeBuffer(fnode)
        assert fnb.total_nrows() == 11

    def test_fnbReadBuffer(self, fnode):
        # The filenode buffer
        fnb = fnbuffer.FilenodeBuffer(fnode)
        fnb.readBuffer(0, 100)
        assert fnb.chunk[0] == ('This is a line inserted programmatically '
                                'at position 0\n')
        assert fnb.chunk[-1] == 'This is the last line.\n'

    def test_fnbGetCell(self, fnode):
        # The filenode buffer
        fnb = fnbuffer.FilenodeBuffer(fnode)
        fnb.readBuffer(0, 100)
        assert fnb.getCell(2, 5) == ('This is a line inserted '
                                     'programmatically at position 2\n')
