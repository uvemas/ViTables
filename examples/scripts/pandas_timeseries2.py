#!/usr/bin/env python3

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

"""Storing time series created with Pandas in PyTables. Example 2.
"""

import datetime
import os

import pandas as pd
import pandas_datareader.data as web

start = datetime.date(2002, 1, 5)
end = datetime.date(2003, 12, 1)

# Retrieve inflation data from FRED
inflation = web.DataReader(['CPIAUCSL', 'CPILFESL'], 'fred', start, end)

# Create an empty HDFStore
output_dir = '../timeseries'
hdf5_name = 'pandas_test2.hdf5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
try:
    os.mkdir(output_dir)
except OSError:
    pass
finally:
    store = pd.HDFStore(filepath_hdf5)

# Store the extracted data as a PyTables Table under the group fred_inflation
store.append('fred_inflation', inflation)
store.close()
