#!/usr/bin/env python
# -*- coding: utf-8 -*-


########################################################################
#
#       Copyright (C) 2008 Vicent Mas. All rights reserved
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
#
########################################################################

"""Plugin that provides basic support for the scikits.timeseries module.

In particular it allows for nicely formatting the time series contained
in PyTables tables generated via scikits.timeseries.
"""

__docformat__ = 'restructuredtext'

import time

import tables

try:
    import scikits.timeseries as ts
except ImportError:
    pass

class TSFormatter(object):
    """An inspector class intended for finding out if a Leaf instance contains
    a time serie and formatting it in a user friendly way.
    """

    def __init__(self, data):
        """The class constructor.

        :Parameter data: the Leaf instance being inspected
        """

        self.leaf = data
        self.ts_kind = self.findTS()
        self.ts_positions = self.tsPosition()
        self.ts_frequency = self.tsFrequency()
        self.formatTime = self.timeFormatter()


    
    def findTS(self):
        """Find out if the inspected leaf contains a time serie.
        """

        ts_kind = None
        if isinstance(self.leaf, tables.Table):
            # Leaf is a PyTables Table
            attrs = self.leaf._v_attrs
            if hasattr(attrs, 'CLASS') and attrs.CLASS == 'TimeSeriesTable':
                # The Table has been created via scikits.timeseries module
                ts_kind = 'scikits_ts'
            else:
                # The Table has been created in a standard way
                for cpath in self.leaf.colpathnames:
                    if self.leaf.coltypes[cpath] in ['time32', 'time64']:
                        ts_kind = 'pytables_ts'
                        break
        else:
            # Leaf is some kind of PyTables array
            atom_type = self.leaf.atom.type
            if atom_type in ['time32', 'time64']:
                ts_kind = 'pytables_ts'
        return ts_kind


    def tsPosition(self):
        """Return the position of every column containing a time serie.
    
        TimeSeriesTable instances contain just one time serie, in a column
        labeled as _dates.
        Regular Table instances can contain any number of time series so we
        must inspect every column.
        Arrays are homogeneous. If a column contains a time serie then every
        column contains a time serie. Specific positions are not required.
        """

        positions = []
        if self.ts_kind == 'scikits_ts':
            positions.append(self.leaf.coldescrs['_dates']._v_pos)
        elif self.ts_kind == 'pytables_ts':
            if isinstance(self.leaf, tables.Table):
                for cpathname in self.leaf.colpathnames:
                    if self.leaf.coltypes[cpathname] in ['time32', 'time64']:
                        positions.append(self.leaf.coldescrs[cpathname]._v_pos)
            else:
                positions = [-1]
        return positions


    def tsFrequency(self):
        """Return the frequency (if any) of the time serie.

        Only time series created via scikits.timeseries module have
        this attribute.
        """

        ts_freq = None
        if self.ts_kind == 'scikits_ts':
            # The frequency of the time serie. Default is 6000 (daily)
            special_attrs = getattr(self.leaf._v_attrs, 'special_attrs', 
                {'freq': 6000})
            ts_freq = special_attrs['freq']
        return ts_freq

    def locateTSModule(self):
        """Find out if the scikits.timeseries module is available.
        """

        is_available = True
        try:
            import scikits.timeseries
        except ImportError:
            is_available = False
        return is_available
    def formatScikitsTS(self, value):
        """Format a given date in a user friendly way.

        Only Date instances (generated via scikits.timeseries module)
        are formatted by this method.

        :Parameter value: the value attribute for the Date object
        """

        date = ts.Date(self.ts_frequency, value=value)
        return date.datetime.strftime('%a %b %d %H:%M:%S %Y')
    def timeFormatter(self):
        """Return the function to be used for formatting time series.
        """

        time_formatter = None
        if self.ts_kind == 'scikits_ts':
            return self.formatScikitsTS
        elif self.ts_kind == 'pytables_ts':
            if isinstance(self.leaf, tables.Table):
                return time.ctime
            else:
                return vitables.utils.formatTimeContent


