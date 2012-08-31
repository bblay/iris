# (C) British Crown Copyright 2010 - 2012, Met Office
#
# This file is part of Iris.
#
# Iris is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Iris is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Iris.  If not, see <http://www.gnu.org/licenses/>.
"""
A package for converting cubes to and from specific file formats.

"""

import pp
import ff
import grib
import netcdf


recognisers = []


def add_recogniser(recogniser):
    """Sorted add. Highest priority values appear first in the list."""
    recognisers.append(recogniser)
    recognisers.sort(key=lambda r: r.priority, reverse=True)


def recognise(basename, file_handle):

    result = None
    cache = {}

    for recogniser in recognisers:
        if file_handle.tell() != 0:
            file_handle.seek(0)
    
        if recogniser.examine(basename, file_handle, cache=cache):
            result = recogniser
            break
    
    if not result:
        raise ValueError('No format specification could be found for the given file:  %s' % basename) 

    file_handle.seek(0)
    return result


add_recogniser(pp.PPRecogniser())
add_recogniser(pp.PPLittleEndianRecogniser())
add_recogniser(grib.GribRecogniser())
add_recogniser(netcdf.NetCDFRecogniser())
add_recogniser(netcdf.NetCDF64OffRecogniser())
add_recogniser(netcdf.NetCDF4Recogniser())
add_recogniser(ff.FF3p1Recogniser())
add_recogniser(ff.FF5p2Recogniser())
