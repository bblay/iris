
import numpy as np
import scipy.spatial


def _min_max_edge(lon_tr_bounds, lat_tr_bounds):
    # Get the largest and smallest edge length in the grid
    lat_diff = np.diff(lat_tr_bounds)
    lon_diff = np.diff(lon_tr_bounds)
    dist = np.sqrt(lat_diff**2 + lon_diff**2)
    dist = np.ma.masked_equal(dist, 0.0)
    return dist.min(), dist.max()


def _nearest_to_point(kdtree, point, shape, segs):
    # Find the nearest point to the given point.
    # Handles co-located points.

    # Get the nearest 3 points.
    near_dists, near_indices = kdtree.query(point, k=3)#, distance_upper_bound=max_edge)

    # Isolate those that are the same.
    near_dists = np.array(near_dists)
    use_these = np.where(near_dists == near_dists[0])
    near_dists = near_dists[use_these]
    near_indices = near_indices[use_these]
    
    # More than one nearest point?
    if len(near_dists) > 1:
        # Get the ij index for each.
        near_ijs = []
        for near_i in near_indices: 
            near_ij = np.array((int(near_i / shape[1]), near_i % shape[1]))
            near_ijs.append(near_ij)

        # Select nearest ij to last point on the current line.
        if len(segs[-1]) > 0:
            diffs = np.sum(np.abs(near_ijs - segs[-1][-1]), axis=1)
            min_i = np.where(diffs == diffs.min())[0]
            near_ij = near_ijs[min_i]
            near_dist = near_dists[min_i]
        else:
            warnings.warn("can't check last point on a new path")
            near_dist = near_dists[0]
            near_ij = near_ijs[0]
        
    # Just one nearest point.
    else:
        near_i = near_indices[0]
        near_dist = near_dists[0]
        near_ij = np.array((int(near_i / shape[1]), near_i % shape[1]))

#     TODO: I think we need to do this...
#     near_ij[0] -= 1
#     near_ij[1] -= 1

    return near_ij, near_dist


def _nearest_to_line(walk_point, shape, segs, lats, lons):
     
    dir = walk_point - segs[-1][-1]
    perp = np.array(dir[1], -dir[0])
    uperp = perp / np.sqrt(np.sum(perp*perp))
    
    to_check = []
    last_ij = segs[-1][-1]
    for y in range(max(0, last_ij[0]-1), min(shape[0], last_ij[0]+1)):
        for x in range(max(0, last_ij[1]-1), min(shape[1], last_ij[1]+1)):
            if x == y == 0:
                continue
            to_check.append((y, x))
            
    dists = [None] * len(to_check)
    for i, p in enumerate(to_check):
        ll = np.array((lats[p], lons[p]))
        dists[i] = abs(np.dot(uperp, ll - walk_point))
    dists = np.array(dists)
    
    near = np.where(dists == dists.min())[0][0]
    return np.array(to_check[near])


def add_point(segs, new_ij):
    if len(segs[-1]) > 0 and np.all(new_ij == segs[-1][-1]):
        raise ValueError("not adding duplicate" + str(new_ij))
    segs[-1].append(new_ij)
    sanity_check_last_points(segs)
    segs[-1] = remove_spike(segs[-1])
    sanity_check_last_points(segs)


def _nearest_corner(point, prev_ij, curr_ij, lon_tr_bounds, lat_tr_bounds):
    ij1 = (prev_ij[0], curr_ij[1])
    ij2 = (curr_ij[0], prev_ij[1])

    pnt1 = np.array((lon_tr_bounds[ij1], lat_tr_bounds[ij1]))
    pnt2 = np.array((lon_tr_bounds[ij2], lat_tr_bounds[ij2]))

    dist1 = np.sqrt(np.sum((pnt1 - point)**2))
    dist2 = np.sqrt(np.sum((pnt2 - point)**2))

    return np.array(ij1 if dist1 < dist2 else ij2)


def check_add_opposite(segs, target_ij, via_near_point, x_bounds, y_bounds):
    # Are we on the opposite corner to the target?
    ijdiff = target_ij - segs[-1][-1]
    if np.all(np.abs(ijdiff) == 1):
        # Add nearest corner so we're one edge away.
        new_ij = _nearest_corner(via_near_point, segs[-1][-1], target_ij,
                                 x_bounds, y_bounds)
        add_point(segs, new_ij)


def remove_spike(path):
    # Remove the end of the path if it goes back on itself.
    if len(path) >= 3:
        if np.array_equal(path[-1], path[-3]):
            print "removing spike"
            path = path[:-2]
    return path


def sanity_check_last_points(segs):
    # Check the end of the path is a single ij step.
    if len(segs[-1]) >= 2:
        ij_diff = segs[-1][-2] - segs[-1][-1]
        if np.sum(np.abs(ij_diff)) != 1:
            seg = segs[-1]
            raise Exception(str(seg[-(min(10,len(seg))):]))

def sanity_check_all_points(segs):
    # sanity check the segs: ensure single u or v steps
    for path in segs:
        for i in range(len(path) - 1):
            ij_diff = path[i] - path[i+1]
            if np.sum(np.abs(ij_diff)) != 1:
                raise Exception("Line walker error " + str(path[i]) + str(path[i+1]))


# TODO: Make sure we can handle >2D cubes (currently fails, I think)
def find_path(cube, line, debug_ax=None):
    start, end = line

    # Make the grid of top-right corners.
    y_coord = cube.coord(axis="Y")
    x_coord = cube.coord(axis="x")
    lat_tr_bounds = y_coord.bounds[..., 2].squeeze()  # TODO: no squeeze
    lon_tr_bounds = x_coord.bounds[..., 2].squeeze()
    shape = lat_tr_bounds.shape

    # Put the corners into a kdtree for fast nearest point searching.
    ll_pairs = zip(lon_tr_bounds.flatten(), lat_tr_bounds.flatten())
    kdtree = scipy.spatial.cKDTree(ll_pairs)

    # Walk the line
    # TODO: adaptive step size?
    min_edge, max_edge = _min_max_edge(lon_tr_bounds, lat_tr_bounds)
    step = max(min_edge / 10.0, 0.01)
    dist_vect = end - start
    line_len = np.sqrt(np.sum(dist_vect**2))
    num_steps = int(line_len / step)  # TODO: do the full length of the line
    segs = [[]]  # List of path tuples

    # Find closest corner points to line
    d = dist_vect / num_steps
    if debug_ax:
        debug_start = 2550
        debug_end = debug_start + 50
        traversed_x = [None] * (debug_end - debug_start + 1)
        traversed_y = [None] * (debug_end - debug_start + 1)
        visited = []
        
    # walk
    for i in range(num_steps):
        
        walk_point = start + d*i
        if debug_ax and debug_start <= i <= debug_end:
            traversed_x[i-debug_start] = walk_point[0]
            traversed_y[i-debug_start] = walk_point[1]
        
        # Are we starting a new line?
        if len(segs[-1]) == 0:

            # Find the nearest point to the walk-point, using the kdtree.
            near_ij, near_dist = _nearest_to_point(kdtree, walk_point, shape, segs)

            # Outside the grid?
            if not np.isfinite(near_dist):
                warnings.warn("Point outside kdtree")
                continue
            
            add_point(segs, near_ij) 
            
        # We are continuging a line.
        else:
            
            # Find the nearest point, from the surrounding 8,
            # to the direction we're heading in.
            near_ij = _nearest_to_line(walk_point, shape, segs, lat_tr_bounds, lon_tr_bounds)
        
            if np.all(near_ij == segs[-1][-1]):
                continue
            check_add_opposite(segs, near_ij, walk_point,
                               lon_tr_bounds, lat_tr_bounds)
            add_point(segs, near_ij)






        if debug_ax and debug_start <= i <= debug_end:
            visited.append((i - debug_start, near_ij))
            seg = segs[-1]
            lat = lat_tr_bounds[near_ij[0], near_ij[1]] 
            lon = lon_tr_bounds[near_ij[0], near_ij[1]] 
            print "{} ({:.3f},{:.3f}) : {}".format(i - debug_start, lon, lat,
                                                   seg[-min(10,len(seg)):])

    if debug_ax:
        debug_ax.plot(traversed_x, traversed_y, "b.")
        for i in range(len(traversed_x)):
            debug_ax.text(traversed_x[i], traversed_y[i], str(i), size="xx-small")
        for i, ij in visited:
            lat = lat_tr_bounds[ij[0], ij[1]] 
            lon = lon_tr_bounds[ij[0], ij[1]] 
            debug_ax.text(lon, lat, "{}: {},{}".format(i, ij[0], ij[1]), size="x-small")



    sanity_check_all_points(segs)
    return segs
