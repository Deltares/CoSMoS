"""Map tile generation for CoSMoS web viewer.

Creates PNG map tiles for flood maps, wave heights, water levels, and other
spatial output variables for display in the CoSMoS web viewer.
"""

from typing import Any, Dict

import numpy as np
from cht_tiling.tiling import make_floodmap_tiles, make_png_tiles

from .cosmos import cosmos

tile_layer: Dict[str, Any] = {}


def make_flood_map_tiles(
    zsmax: np.ndarray,
    index_path: str,
    topo_path: str,
    flood_map_path: str,
    water_level_correction: float = 0.0,
) -> None:
    """Generate flood map tiles from maximum water levels.

    Parameters
    ----------
    zsmax : np.ndarray
        Maximum water level field.
    index_path : str
        Path to the tile index directory.
    topo_path : str
        Path to the topo-bathymetry tile directory.
    flood_map_path : str
        Output path for the generated PNG tiles.
    water_level_correction : float, optional
        Vertical datum offset applied to *zsmax*.
    """
    zsmax += water_level_correction

    mp = next((x for x in cosmos.config.map_contours if x["name"] == "flood_map"), None)
    color_values = mp["contours"]

    make_floodmap_tiles(
        zsmax,
        index_path,
        flood_map_path,
        topo_path,
        option="deterministic",
        color_values=color_values,
        zoom_range=[0, 13],
        zbmax=1.0,
        quiet=True,
    )


def make_wave_map_tiles(
    hm0max: np.ndarray,
    index_path: str,
    wave_map_path: str,
    contour_set: str,
) -> None:
    """Generate wave height map tiles.

    Parameters
    ----------
    hm0max : np.ndarray
        Maximum significant wave height field.
    index_path : str
        Path to the tile index directory.
    wave_map_path : str
        Output path for the generated PNG tiles.
    contour_set : str
        Name of the contour definition to use from the configuration.
    """
    mp = next((x for x in cosmos.config.map_contours if x["name"] == contour_set), None)
    if mp is not None:
        make_png_tiles(
            hm0max,
            index_path,
            wave_map_path,
            color_values=mp["contours"],
            zoom_range=[0, 9],
            quiet=True,
        )


def make_precipitation_tiles(
    pcum: np.ndarray,
    index_path: str,
    p_map_path: str,
    contour_set: str,
) -> None:
    """Generate cumulative precipitation map tiles.

    Values below 1.0 mm are masked out before tiling.

    Parameters
    ----------
    pcum : np.ndarray
        Cumulative precipitation field (mm).
    index_path : str
        Path to the tile index directory.
    p_map_path : str
        Output path for the generated PNG tiles.
    contour_set : str
        Name of the contour definition to use from the configuration.
    """
    pcum[np.where(pcum < 1.0)] = np.nan

    mp = next((x for x in cosmos.config.map_contours if x == contour_set), None)
    if mp is not None:
        make_png_tiles(
            pcum,
            index_path,
            p_map_path,
            color_values=cosmos.config.map_contours[mp]["contours"],
            zoom_range=[0, 10],
            quiet=True,
        )


def make_sedero_tiles(
    sedero: np.ndarray, index_path: str, sedero_map_path: str
) -> None:
    """Generate sedimentation/erosion map tiles.

    Parameters
    ----------
    sedero : np.ndarray
        Sedimentation/erosion field.
    index_path : str
        Path to the tile index directory.
    sedero_map_path : str
        Output path for the generated PNG tiles.
    """
    mp = next((x for x in cosmos.config.map_contours if x["name"] == "sedero"), None)
    if mp is not None:
        make_png_tiles(
            sedero,
            index_path,
            sedero_map_path,
            color_values=mp["contours"],
            zoom_range=[0, 16],
            quiet=True,
        )


def make_bedlevel_tiles(
    bedlevel: np.ndarray, index_path: str, bedlevel_map_path: str
) -> None:
    """Generate bed level map tiles.

    Parameters
    ----------
    bedlevel : np.ndarray
        Bed level field.
    index_path : str
        Path to the tile index directory.
    bedlevel_map_path : str
        Output path for the generated PNG tiles.
    """
    mp = next(
        (x for x in cosmos.config.map_contours if x["name"] == "bed_levels"), None
    )
    if mp is not None:
        make_png_tiles(
            bedlevel,
            index_path,
            bedlevel_map_path,
            color_values=mp["contours"],
            zoom_range=[0, 16],
            quiet=True,
        )
