# this file processes the geometry and finds an optimal mapping of positions
# of maximum number of modules on a surface


# import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
import numpy as np
# from cadaster.__main__ import get_building
import math


def smooth_shape(shape):
    res = shape[:]
    for i in range(len(res) - 1):
        if np.sqrt((res[i][0] - res[i + 1][0]) ** 2 + (res[i][1] - res[i + 1][1]) ** 2) <= 0.5:  # 0.707:
            res[i + 1] = [(res[i][0] + res[i + 1][0]) / 2, (res[i][1] + res[i + 1][1]) / 2]

    return res


def smooth_shape_n(shape, n):
    res = shape
    for _ in range(n):
        res = smooth_shape(res)
    return res


def get_centroid(shape):
    x = 0
    y = 0
    for i in range(len(shape)):
        x += shape[i][0]
        y += shape[i][1]
    x /= len(shape)
    y /= len(shape)
    return x, y


def center_shape(shape, around=None):
    if around is None:
        around = get_centroid(shape)
    return [[point[0] - around[0], point[1] - around[1]] for point in shape], around


def euclidean_distance(point0, point1):
    return np.sqrt(
        (point0[0] - point1[0])**2 + (point0[1] - point1[1])**2
    )


# options: scale [0..1], meters [-N, N]
def scale_shape(shape, **options):
    new_shape, around = center_shape(shape)
    if "scale" in options:
        scale = options["scale"]
    elif "meters" in options:
        dist = euclidean_distance([0, 0], new_shape[0])
        scale = (dist - options["meters"])/dist
    else:
        raise NameError("Unknown parameter for scaling!")

    scale = max(0.1, scale)
    return [[point[0] * scale + around[0], point[1] * scale + around[1]] for point in new_shape]


def rotate_point(point, angle):
    x = point[0] * np.cos(angle * np.pi / 180) - point[1] * np.sin(angle * np.pi / 180)
    y = point[0] * np.sin(angle * np.pi / 180) + point[1] * np.cos(angle * np.pi / 180)
    return x, y


def rotate_shape(shape, angle):
    return [rotate_point(point, angle) for point in shape]


def intersects(shape1, shape2):
    polygon1 = Polygon(shape2)
    for point in shape1:
        if polygon1.contains(Point(point)):
            return True

    polygon2 = Polygon(shape1)
    for point in shape2:
        if polygon2.contains(Point(point)):
            return True

    if polygon1.contains(polygon2.centroid):
        return True

    if polygon2.contains(polygon1.centroid):
        return True

    return False


def is_inside(shape1, shape2):
    res = True
    polygon1 = Polygon(shape2)
    for point in shape1:
        res = res and polygon1.contains(Point(point))
        if res is False:
            break

    polygon2 = Polygon(shape1)
    for point in shape2:
        res = res and not polygon2.contains(Point(point))
        if res is False:
            break

    if not polygon1.contains(polygon2.centroid):
        return False

    for a_x, a_y in shape1:
        c_x, c_y = polygon2.centroid.xy
        x, y = (a_x + c_x[0])/2, (a_y + c_y[0])/2
        if not polygon1.contains(Point(x, y)):
            return False

    return res


def translate_shape(shape, x, y):
    res = shape[:]
    for i in range(len(res)):
        res[i] = [res[i][0] + x, res[i][1] + y]
    return res


def get_shape_bottom(shape):
    return min([y for x, y in shape])


def get_shape_top(shape):
    return max([y for x, y in shape])


def get_shape_bounds(shape):
    xs, ys = list(zip(*shape))
    return min(xs), min(ys), max(xs), max(ys)


def get_new_rect(width: float, height: float):
    dw = width / 2
    dh = height / 2
    return [
        [-dw, dh],
        [dw, dh],
        [dw, -dh],
        [-dw, -dh],
        [-dw, dh],
    ]


def sweep_north(mother_shape, x, rect_width, rect_height, y1, y2, resl, surfaces=[]):
    rectangle = get_new_rect(width=rect_width, height=rect_height)
    rectangle = translate_shape(rectangle, x, 0)

    for dy in range(int(y1 * resl), int(y2 * resl)):
        rect_t = translate_shape(rectangle, 0, dy / resl)
        if is_inside(rect_t, mother_shape) and all([not intersects(rect_t, sub_surface) for sub_surface in surfaces]):
            return rect_t

    return None


def get_max_at(mother_shape, x, rect_width, rect_height, resl=4, surfaces=[]):
    # up
    x1, y1, x2, y2 = get_shape_bounds(mother_shape)
    rects = []

    new_rect = sweep_north(mother_shape, x, rect_width, rect_height, y1, y2, resl, surfaces=surfaces)

    if new_rect:
        rects.append(new_rect)

    if len(rects) == 0:
        return []
    top = get_shape_top(rects[-1])

    while True:
        new_rect = get_new_rect(width=rect_width, height=rect_height)
        new_rect = translate_shape(new_rect, x, top + rect_height / 2)
        if is_inside(new_rect, mother_shape):
            if all([not intersects(new_rect, sub_surface) for sub_surface in surfaces]):
                rects.append(new_rect)
                top += rect_height
            else:
                top += 1/resl
        else:
            break

    return rects



def f_fit_fixed(shape, orientation, rect_width, rect_height, resl=20, surfaces=[]):

    rotation_angle = orientation + 180  # to start from below

    # center the shape
    centered_surface, center = center_shape(shape[:])

    # smooth twice
    centered_surface = smooth_shape(smooth_shape(centered_surface))
    centered_surface = rotate_shape(centered_surface, rotation_angle)

    # do the same for every subsurface
    centered_subsurfaces = []
    for subsurface in surfaces:
        centered_subsurface, _ = center_shape(subsurface[:], around=center)
        centered_subsurface = smooth_shape(smooth_shape(centered_subsurface))
        centered_subsurface = rotate_shape(centered_subsurface, rotation_angle)
        centered_subsurfaces.append(centered_subsurface)


    rects = []
    x1, y1, x2, y2 = get_shape_bounds(centered_surface)

    for x in range(int(x1 * resl), int(x2 * resl), math.ceil(rect_width * resl)):
        rects += get_max_at(centered_surface, x / resl - 0.5, rect_width, rect_height, resl=resl, surfaces=centered_subsurfaces)

    # translate and rotate back
    for i in range(len(rects)):
        rects[i] = rotate_shape(rects[i], -rotation_angle)
        rects[i] = translate_shape(rects[i], center[0], center[1])

    return rects





def fit_fixed_exact(mother_shape, orientation, rect_width, recht_height, resl=4, shadow_offset=0, subsurfaces=None):
    if subsurfaces is None:
        subsurfaces = []

    rotation_angle = orientation + 180  # to start from below

    # center the shape
    centered_surface, center = center_shape(mother_shape)

    # smooth twice
    centered_surface = smooth_shape(smooth_shape(centered_surface))
    centered_surface = rotate_shape(centered_surface, rotation_angle)
    x1, y1, x2, y2 = get_shape_bounds(centered_surface)

    # do the same for every subsurface
    centered_subsurfaces = []
    for subsurface in subsurfaces:
        centered_subsurface, _ = center_shape(subsurface[:], around=center)
        centered_subsurface = smooth_shape(smooth_shape(centered_subsurface))
        centered_subsurface = rotate_shape(centered_subsurface, rotation_angle)
        centered_subsurface = scale_shape(centered_subsurface, meters=shadow_offset)
        centered_subsurfaces.append(centered_subsurface)


    rects = []
    half_width = rect_width / 2.0
    half_height = recht_height / 2.0
    for y_shift in range(int(-half_height*resl), int(half_height*resl)):
        surfs_temp_y = []
        for x_shift in range(int(-half_width*resl), int(half_width*resl)):
            surfs_temp = []
            for x in range(int(x1), int(x2/rect_width+1)):
                for y in range(int(y1), int(y2/recht_height+1)):
                    rectangle = get_new_rect(width=rect_width, height=recht_height)
                    rectangle = translate_shape(rectangle, x*rect_width + x_shift/resl, y*recht_height + y_shift/resl)
                    if is_inside(rectangle, centered_surface) and all([not intersects(rectangle, sub_surface) for sub_surface in centered_subsurfaces]):
                        surfs_temp.append(rectangle)

            if len(surfs_temp) > len(surfs_temp_y):
                surfs_temp_y = list.copy(surfs_temp)

        if len(surfs_temp_y) > len(rects):
            rects = list.copy(surfs_temp_y)

    # translate and rotate back
    for i in range(len(rects)):
        rects[i] = rotate_shape(rects[i], -rotation_angle)
        rects[i] = translate_shape(rects[i], center[0], center[1])

    return rects


def f_fit(shape, orientation, rect_width, rect_height, resl=2, shadow_offset=0, surfaces=[]):
    rects_vert = fit_fixed_exact(shape, orientation, rect_width, rect_height, shadow_offset=shadow_offset, resl=resl, subsurfaces=surfaces)
    rects_horz = fit_fixed_exact(shape, orientation, rect_height, rect_width, shadow_offset=shadow_offset, resl=resl, subsurfaces=surfaces)

    if len(rects_vert) >= len(rects_horz):
        return rects_vert
    else:
        return rects_horz


