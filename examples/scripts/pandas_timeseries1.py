#!/usr/bin/env python2
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

"""Storing time series created with Pandas in PyTables. Example 1.
"""

import os

import numpy as np
import pandas as pd

## A test series, the deprecated way (not supported by timeseries plugin)
#startdate = pd.Period(freq='D', year=2009, month=1, day=1)
#rng = pd.period_range(startdate, periods=365)
#ts = pd.Series(np.arange(1, 366), index=rng)

## A test series, the recommended way
dti = pd.DatetimeIndex(start='1/1/2009', freq='D', periods=365)
ts = pd.Series(np.arange(1, 366), index=dti)
# Saving this time series in a HDFStore will add two arrays to the h5 file
# one array with the index and other with the data
# So we create a data frame in order to store all the information in a table
df = pd.DataFrame(ts)

# Write to a PyTables file
output_dir = '../timeseries'
try:
    os.mkdir(output_dir)
except OSError:
    pass

hdf5_name = 'pandas_test1.hdf5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
store = pd.HDFStore(filepath_hdf5)

# The following code create a group with 1 leaf (Table instance)
# df
#  |_ table
store.append('one_column_ts', df)
store.close()

