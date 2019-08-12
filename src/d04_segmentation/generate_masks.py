from time import time

import numpy as np
import pandas as pd

from shapely.geometry import Polygon
from skimage.draw import polygon

from d00_utils.db_utils import dbReadWriteViews


def get_lines(row):
    """Get lines from start and end coordinates.
    
    Output format: [((x1, y1), (x2, y2)), ...]
    
    :param row: measurement segments grouped by instance and index
    :return: line coordinates
    """

    x1s, y1s, x2s, y2s = (
        row["x1coordinate"],
        row["y1coordinate"],
        row["x2coordinate"],
        row["y2coordinate"],
    )
    start_points, end_points = tuple(zip(x1s, y1s)), tuple(zip(x2s, y2s))
    lines = list(zip(start_points, end_points))
    return lines


# TODO: Join outer points using spline curves?
def get_points(row):
    """Get outer points of polygon from chord lines.
    
    Output format: [(x1, y1), (x2, y2), ...]
    
    The "Eje largo" chord line is first and perpendicular to the "Disco" chord lines.
    
    Start at one end of "Eje largo" line, cycle through one end of "Disco" lines,
    then cycle back through other end of "Eje largo"/"Disco" lines, ending at start point.
    
    :param: measurement segments grouped by instance and index
    :return: point coordinates
    """

    eje_largo_line = row["lines"][0]
    discos_lines = row["lines"][1:]

    eje_largo_start = eje_largo_line[0]
    eje_largo_end = eje_largo_line[1]

    discos_starts = [line[0] for line in discos_lines]
    discos_ends = [line[1] for line in discos_lines]

    points = [eje_largo_start]
    points += discos_starts
    points += [eje_largo_end]
    points += reversed(discos_ends)
    points += [eje_largo_start]
    return points


def get_mask(row):
    """Get Numpy mask from polygon specified by points.
    
    :param: measurement segments grouped by instance and index
    :return: Numpy mask
    """

    poly = Polygon(row["points"])
    exterior = list(poly.exterior.coords)

    # https://scikit-image.org/docs/dev/api/skimage.draw.html#skimage.draw.polygon
    c = [pt[0] for pt in exterior]
    r = [pt[1] for pt in exterior]
    rr, cc = polygon(r, c)

    # TODO: get shape from DICOM metadata, which needs to be updated.
    SHAPE = (600, 800)
    img = np.zeros(SHAPE, dtype=np.uint8)
    img[rr, cc] = 1

    return img


def generate_masks():
    """Convert measurement segments to Numpy masks.
    
    :return: updated DataFrame
    """

    io_views = dbReadWriteViews()

    chords_by_volume_mask_df = io_views.get_table("chords_by_volume_mask")
    instances_w_labels_test_downsampleby5_df = io_views.get_table('instances_w_labels_test_downsampleby5')    
    chords_by_volume_mask_df.loc[chords_by_volume_mask_df["view_name"].str.contains('ven'), "chamber"] = "lv"
    chords_by_volume_mask_df.loc[chords_by_volume_mask_df["view_name"].str.contains('atr'), "chamber"] = "la"
    
    merge_df = chords_by_volume_mask_df.merge(instances_w_labels_test_downsampleby5_df, on='instanceidk')

    start = time()
    group_df = merge_df.groupby(["instanceidk", "indexinmglist"]).agg(
        {
            "x1coordinate": list,
            "y1coordinate": list,
            "x2coordinate": list,
            "y2coordinate": list,
            "chamber": pd.Series.unique,
            "frame": pd.Series.unique,
            "filename": pd.Series.unique
        }
    )
    end = time()
    print(f"{int(end-start)} seconds to group {len(merge_df)} rows")

    start = time()
    group_df["lines"] = group_df.apply(get_lines, axis=1)
    group_df["points"] = group_df.apply(get_points, axis=1)
    group_df["mask"] = group_df.apply(get_mask, axis=1)
    group_df = group_df.reset_index()
    end = time()
    print(f"{int(end-start)} seconds to apply {len(group_df)} rows")

    return group_df