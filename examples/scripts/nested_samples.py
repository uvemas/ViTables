# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2011 Vicent Mas. All rights reserved
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
#       This script is based on a set of scripts by Francesc Alted.

"""A Table with nested records."""

import random

import tables

fileout = "nested_samples.h5"

# An example of enumerated structure
colors = tables.Enum(['red', 'green', 'blue'])

def write(h5file, desc, indexed):
    fileh = tables.openFile(h5file, "w")
    table = fileh.createTable(fileh.root, 'table', desc)
    #for colname in indexed:
    #    table.colinstances[colname].createIndex()

    row = table.row
    for i in range(10):
        row['x'] = i
        row['y'] = 10.2-i
        row['z'] = i
        row['color'] = colors[random.choice(['red', 'green', 'blue'])]
        row['extra_info/name'] = "name%s" % i
        row['extra_info/info2/info3/z4'] =  i
        # All the rest will be filled with defaults
        row.append()

    fileh.close()

# The sample nested class description

class Info(tables.IsDescription):
    _v_pos = 2
    Name = tables.StringCol(16, dflt='sample string')
    Value = tables.Float64Col()

class Test(tables.IsDescription):
    """A description that has several columns"""
    x = tables.Int32Col(shape=2, dflt=0, pos=0)
    y = tables.Float64Col(dflt=1.2, shape=(2, 3))
    z = tables.UInt8Col(dflt=1)
    color = tables.EnumCol(colors, 'red', base='uint32', shape=(2,))
    Info = Info()
    class extra_info(tables.IsDescription):
        _v_pos = 1
        name = tables.StringCol(10)
        value = tables.Float64Col(pos=0)
        y2 = tables.Float64Col(dflt=1, shape=(2, 3), pos=1)
        z2 = tables.UInt8Col(dflt=1)
        class info2(tables.IsDescription):
            y3 = tables.Float64Col(dflt=1, shape=(2, 3))
            z3 = tables.UInt8Col(dflt=1)
            name = tables.StringCol(10)
            value = tables.EnumCol(colors, 'blue', base='uint32', shape=(1,))
            class info3(tables.IsDescription):
                name = tables.StringCol(10)
                value = tables.Time64Col()
                y4 = tables.Float64Col(dflt=1, shape=(2, 3))
                z4 = tables.UInt8Col(dflt=1)

# Write the file and read it
write(fileout, Test, ['info/info2/z3'])
