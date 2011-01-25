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
Example 1.
"""

import os

import numpy as np

import scikits.timeseries as ts
import scikits.timeseries.lib.tstables as tstab
import scikits.timeseries.lib.reportlib as rl

## a test series
data = np.arange(1, 366)
startdate = ts.Date(freq='D', year=2009, month=1, day=1)
test_series = ts.time_series(data, start_date=startdate, freq='D')

output_dir = '../timeseries'
try:
    os.mkdir(output_dir)
except OSError:
    pass

## write to csv file
csv_file = os.path.abspath(os.path.join(output_dir, 'test_series.csv'))
mycsv = open(csv_file, 'w')
csvReport = rl.Report(test_series, delim=';',
fixed_width=True)
csvReport(output=mycsv)
mycsv.close()

# Write to a PyTables file
hdf5_name = 'scikits_test1.hdf5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
h5file = tstab.openFile(filepath_hdf5, mode="w",
title='Example table with csikits time series')
group_doc = h5file.createGroup("/", 'examples', 'Test Data')
table = h5file.createTimeSeriesTable(group_doc, 'Example_1', test_series)
h5file.close()
