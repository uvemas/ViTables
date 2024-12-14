#!/usr/bin/env python3

#       Copyright (C) 2008-2024 Vicent Mas. All rights reserved
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

import numpy as np
import numpy.random as nr
import pandas as pd

# A multiindexed dataframe with 3 columns of data (including a time series)
dti = list(pd.date_range('1/1/2019', periods=365, freq='D'))
ordinal = list(np.arange(1, 6))
iterables = [dti, ordinal]
index = pd.MultiIndex.from_product(iterables, names=['first', 'second'])
d = {'A': nr.randn(1825),
     'B': nr.randn(1825),
     'C': pd.date_range('1/1/2017', periods=1825)}
df = pd.DataFrame(d, index=index)

# Create an empty HDFStore
output_dir = '../timeseries'
hdf5_name = 'pandas_test3.hdf5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
try:
    os.mkdir(output_dir)
except OSError:
    pass
finally:
    store = pd.HDFStore(filepath_hdf5)

# Store the dataframe as a PyTables Table under the group df_table
store.append('df_table', df)
store.close()
