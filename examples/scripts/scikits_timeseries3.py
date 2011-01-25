# -*- coding: utf-8 -*-
#!/usr/bin/env python

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

"""Storing time series created with scikits.timeseries module in PyTables.
Example 3.
"""

import os

import numpy as np

import scikits.timeseries as ts
import scikits.timeseries.lib.tstables as tstab

# Generate random data
data = np.cumprod(1 + np.random.normal(0, 1, 300)/100)
series = ts.time_series(data, start_date=ts.Date(freq='M', year=1982, month=1))

# Write to a PyTables file
output_dir = '../timeseries'
try:
    os.mkdir(output_dir)
except OSError:
    pass

hdf5_name = 'scikits_test3.hdf5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
h5file = tstab.openFile(filepath_hdf5, mode="w",
title='Example table with csikits time series')
group_doc = h5file.createGroup("/", 'examples', 'Test Data')
table = h5file.createTimeSeriesTable(group_doc, 'Example_3', series)
h5file.close()
