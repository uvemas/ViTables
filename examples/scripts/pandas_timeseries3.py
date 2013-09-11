#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2008-2013 Vicent Mas. All rights reserved
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

"""Storing time series created with Pandas in PyTables. Example 3.
"""

import os

import numpy.random as nr
import pandas

## a test data frame with 3 column and 365 rows
index = pandas.date_range('1/1/2009', periods=365, freq='D')
df = pandas.DataFrame(nr.randn(365, 3), index=index, columns=['A', 'B', 'C'])

# Write to a PyTables file
output_dir = '../timeseries'
try:
    os.mkdir(output_dir)
except OSError:
    pass

hdf5_name = 'pandas_test3.hdf5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
store = pandas.HDFStore(filepath_hdf5)

# The following code create a group with 4 leaves (Array instances)
# df
#  |_ axis1 (the row index, a range of dates, shape is (365,))
#  |_ axis0 (the column index, shape is (3,))
#  |_ block0_values (the random array of values, shape is (365,3))
#  |_ block0_items (identical to axis0)
store['df'] = df

# The following code stores the same information in a Table instance
# df_table
#        |_ table (field index contains the range of dates used as index, field
#                  values_block0 contains the random array of values,
#                  shape is (365,))
store.append('df_table', df)
store.close()

