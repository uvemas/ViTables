#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

"""Storing time series created with Pandas in PyTables. Example 2.
"""

import os
import datetime

import pandas
import pandas_datareader.data as web

startdate = datetime.date(2002, 1, 5)
enddate = datetime.date(2003, 12, 1)

# Retrieve data from Google Finance
# Data format is [(d, [open, high, low, close], volume), ...]
google_f = web.DataReader('F', 'google', startdate, enddate)

# Write to a PyTables file
output_dir = '../timeseries'
try:
    os.mkdir(output_dir)
except OSError:
    pass

hdf5_name = 'pandas_test2.hdf5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
store = pandas.HDFStore(filepath_hdf5)

# The following code stores the information in a Table instance
# intc
#    |_ table (field index contains the dates range used as index, field
#              values_block0 contains [open, high, low, close, adj close],
#              field values_block1 contains volume
#              shape is (480,))
store.append('google_f', google_f)
store.close()

