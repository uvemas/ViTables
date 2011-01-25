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
Example 2.

Notes:
 -The dates from the yahoo quotes module get returned as integers, which happen
  to correspond to the integer representation of 'DAILY' frequency dates in the
  scikits.timeseries module.
 -`fill_missing_dates` will insert masked values for any missing data points.
  Note that you could plot the series without doing this, but it would cause
  missing values to be linearly interpolated rather than left empty in the plot
"""

import os
import datetime

from matplotlib.finance import quotes_historical_yahoo
import scikits.timeseries as ts
import scikits.timeseries.lib.tstables as tstab

startdate = datetime.date(2002, 1, 5)
enddate = datetime.date(2003, 12, 1)

# retrieve data from yahoo.
# Data format is [(d, open, close, high, low, volume), ...] where d is
# a floating point representation of the number of days since 01-01-01 UTC
quotes = quotes_historical_yahoo('INTC', startdate, enddate)

# Create a DateArray of daily dates and convert it to business day frequency
dates = ts.date_array([q[0] for q in quotes], freq='DAILY').asfreq('BUSINESS')

opens = [q[1] for q in quotes]

# opens: the data portion of the timeserie
# dates: the date portion of the timeserie
raw_series = ts.time_series(opens, dates)
test_series = raw_series
#test_series = ts.fill_missing_dates(raw_series, fill_value=-1)

# Write to a PyTables file
output_dir = '../timeseries'
try:
    os.mkdir(output_dir)
except OSError:
    pass

hdf5_name = 'scikits_test2.hdf5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
h5file = tstab.openFile(filepath_hdf5, mode="w",
title='Example table with csikits time series')
group_doc = h5file.createGroup("/", 'examples', 'Test Data')
table = h5file.createTimeSeriesTable(group_doc, 'Example_2', test_series)
h5file.close()
