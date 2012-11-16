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


# import iris tests first so that some things can be initialised before importing anything else
import iris.tests as tests

import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs

import iris
import iris.plot as iplt
import iris.quickplot as qplt


@iris.tests.skip_data
class TestLoad(tests.GraphicsTest):
    
#    def test_load(self):
#        cube = iris.load(tests.get_data_path(('NIMROD', 'uk2km', 'WO0000000003452',
#                        '201007020900_u1096_ng_ey00_visibility0180_screen_2km')))[0]
#        self.assertCML(cube, ("nimrod", "load.cml"))
#        
#        c = plt.contourf(cube.data, levels=np.linspace(-25000, 6000, 10))
#        self.check_graphic()
        
    def test_korean(self):
#        cubes = iris.load(tests.get_data_path(('NIMROD', 'Korea', '201210240000_k0880_ll_umqg_height0000_orography_2km')))
        cube = iris.load_cube('/data/local/dataZoo/NIMROD/Korea/201210240000_k0880_ll_umqg_height0000_orography_2km')
        self.assertCML(cube, ("nimrod", "korean.cml"))
        
        qplt.contourf(cube)
        plt.gcs().coastlines()
        self.check_graphic()

if __name__ == "__main__":
    tests.main()
