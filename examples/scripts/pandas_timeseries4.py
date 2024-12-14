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

"""Storing time series created with Pandas in PyTables. Example 4.
"""

import os

import numpy as np
import pandas as pd

# Create a DataFrame with a DateTimeIndex and linear data
dti = pd.date_range(start='1/1/2019', periods=365, name='Day', freq='D')
ts = pd.Series(np.arange(1, 366), index=dti)
df = pd.DataFrame(ts, columns=["day"])

dti2 = pd.date_range(start='1/1/2019', periods=12, name='Month', freq='ME')
ts2 = pd.Series(np.arange(1, 13), index=dti2)
df2 = pd.DataFrame(ts2, columns=["month"])

dti3 = pd.date_range(start='1/1/2019', periods=52, name='Week', freq='W')
ts3 = pd.Series(np.arange(1, 53), index=dti3)
df3 = pd.DataFrame(ts3, columns=["week"])

# Create an empty HDFStore
output_dir = '../timeseries'
hdf5_name = 'pandas_test4.hdf5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
try:
    os.mkdir(output_dir)
except OSError:
    pass
finally:
    store = pd.HDFStore(filepath_hdf5)

# Store the dataframes as a PyTables Table under the root group
store.append('', df2)
store.append('/', df2)
store.append('df', df)
store.append('df3', df3)
store.close()
