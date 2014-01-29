# (C) British Crown Copyright 2013, Met Office
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
"""Unit tests for the iris.fileformats.grib.grib_save_rules data function."""

# import iris tests first so that some things can be initialised before
# importing anything else
import iris.tests as tests

import gribapi
import numpy as np
import numpy.ma as ma

from iris.fileformats.grib import GribWrapper
from iris.fileformats.grib.grib_save_rules import data
import iris.tests.stock


class TestMdi(tests.IrisTest):

    def setUp(self):
        iris.fileformats.grib.hindcast_workaround = True

        self.cube = iris.tests.stock.global_grib2()
        data = np.arange(self.cube.data.size, dtype=np.float)
        self.cube.data = ma.array(data.reshape(self.cube.data.shape))

        self.grib = GribWrapper(gribapi.grib_new_from_samples("GRIB2"))

    def tearDown(self):
        iris.fileformats.grib.hindcast_workaround = False

    def test_nan(self):
        # Test with a nan fill value.
        self.cube.data[0:10, 0:10] = np.nan
        self.cube.data = ma.masked_invalid(self.cube.data)
        data(self.cube, self.grib.grib_message)
        self.assertEqual(self.grib.numberOfMissing, 100)

    def test_out_of_range(self):
        # Test with a fill value outside the data range.
        self.cube.data.fill_value = -10
        data(self.cube, self.grib.grib_message)
        self.assertEqual(self.grib.numberOfMissing, 0)

    def test_in_range(self):
        # Test with a fill value that appears in the data.
        self.cube.data[0:10, 0:10] = -10
        self.cube.data.fill_value = -10
        data(self.cube, self.grib.grib_message)
        self.assertEqual(self.grib.numberOfMissing, 100)


if __name__ == "__main__":
    tests.main()
