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

import struct
import os

import pp
import ff
import grib
import netcdf
#import nimrod


class Recogniser(object):
    """Abstract base class for recognising a file format."""
    def __init__(self):
        self.title = None
        """Description of format."""
        
        self.priority = 0
        """Lower value = lower priority."""
        
        self.loader = None
        """Function to load from the file format."""

    def examine(self, filename, file_handle, cache=None):
        """Return True if the file is recognised, else False.
        
        Called by the :func:`iris.load` framework.
        
        Args:
        
            * filename    - filename to optioanlly examine 
            * file_handle - file_handle to optionally examine
            
        Kwargs:
        
            * cache - for faster operation, this can be used in conjunction with
                      :func:`~Recogniser.magic32` and :func:`~Recogniser.magic64`.
        
        """
        raise NotImplementedError()

    def __str__(self):
        return "%s (priority %s)" % (self.title, self.priority)
    
    # helper functions with optional cache
    def magic32(self, file_handle, cache=None):
        """Read a 32-bit number from the file, if not already in the optional cache."""
        result = None
        if cache:
            key = "magic32"
            result = cache.get(key)
        if not result:
            result = struct.unpack('>L', file_handle.read(4))[0]
        if cache:
            cache[key] = result
        return result
            
    def magic64(self, file_handle, cache=None):
        """Read a 64-bit number from the file, if not already in the optional cache."""
        result = None
        if cache:
            key = "magic64"
            result = cache.get(key)
        if not result:
            result = struct.unpack('>Q', file_handle.read(8))[0]
        if cache:
            cache[key] = result
        return result


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


# File format recognisers

    
class PPRecogniser(Recogniser):
    """Recognise PP files."""
    def __init__(self):
        self.title = 'UM Post Processing file (PP)'
        self.priority = 5
        self.loader = pp.load_cubes
    
    def examine(self, filename, file_handle, cache):
        return self.magic32(file_handle, cache) == 0x00000100


class PPLittleEndianRecogniser(Recogniser):
    """Recognise PP files."""
    def __init__(self):
        self.title = 'UM Post Processing file (PP) little-endian'
        self.priority = 5
        self.loader = self.loader
    
    def examine(self, filename, file_handle, cache):
        return self.magic32(file_handle, cache) == 0x00010000

    def loader(self, filename, *args, **kwargs):
        raise ValueError('PP file %r contains little-endian data, please convert to big-endian with command line utility "bigend".' % filename)


class GribRecogniser(Recogniser):
    """Recognise GRIB files."""
    def __init__(self):
        self.title = 'GRIB' 
        self.priority = 5
        self.loader = grib.load_cubes
    
    def examine(self, filename, file_handle, cache):
        return self.magic32(file_handle, cache) == 0x47524942


class NetCDFRecogniser(Recogniser):
    """Recognise NetCDF files."""
    def __init__(self):
        self.title = 'NetCDF' 
        self.priority = 5
        self.loader = netcdf.load_cubes
    
    def examine(self, filename, file_handle, cache):
        return self.magic32(file_handle, cache) == 0x43444601


class NetCDF64OffRecogniser(Recogniser):
    """Recognise NetCDF 64-bit offset files."""
    def __init__(self):
        self.title = 'NetCDF 64 bit offset format'
        self.priority = 5
        self.loader = netcdf.load_cubes
    
    def examine(self, filename, file_handle, cache):
        return self.magic32(file_handle, cache) == 0x43444602


class NetCDF4Recogniser(Recogniser):
    """Recognise NetCDF 4 files.
    
    NOTE: this covers both v4 and v4 "classic model", the signature is the same
    
    """
    def __init__(self):
        self.title = 'NetCDF_v4'
        self.priority = 5
        self.loader = netcdf.load_cubes
    
    def examine(self, filename, file_handle, cache):
        return self.magic64(file_handle, cache) == 0x894844460d0a1a0a


class FF3p1Recogniser(Recogniser):
    """Recognise UM Fields files (pre v3.1)."""
    def __init__(self):
        self.title = 'UM Fields file (FF) pre v3.1'
        self.priority = 4
        self.loader = ff.load_cubes
    
    def examine(self, filename, file_handle, cache):
        return self.magic64(file_handle, cache) == 0x0000000000000014


class FF5p2Recogniser(Recogniser):
    """Recognise UM Fields files (post v5.2)."""
    def __init__(self):
        self.title = 'UM Fields file (FF) post v5.2'
        self.priority = 4
        self.loader = ff.load_cubes
    
    def examine(self, filename, file_handle, cache):
        return self.magic64(file_handle, cache) == 0x000000000000000F


#class NIMRODRecogniser(Recogniser):
#    """Recognise NIMROD files."""
#    def __init__(self):
#        self.title = 'NIMROD'
#        self.priority = 5
#        self.loader = nimrod.load_cubes
#    
#    def examine(self, filename, file_handle, cache):
#        """A more complex recognition."""
#
#        # Test for header wrapper
#        if self.magic32(file_handle, cache) != 512:
#            return False
#        file_handle.seek(512, os.SEEK_CUR)
#        if self.magic32(file_handle, cache) != 512:
#            return False
#        
#        # Test for field wrapper
#        length = self.magic32(file_handle, cache)
#        file_handle.seek(length, os.SEEK_CUR)
#        if self.magic32(file_handle, cache) != length:
#            return False
#
#        return True
        


add_recogniser(PPRecogniser())
add_recogniser(PPLittleEndianRecogniser())
add_recogniser(GribRecogniser())
add_recogniser(NetCDFRecogniser())
add_recogniser(NetCDF64OffRecogniser())
add_recogniser(NetCDF4Recogniser())
add_recogniser(FF3p1Recogniser())
add_recogniser(FF5p2Recogniser())
#add_recogniser(NIMRODRecogniser())
