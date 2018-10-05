#!/usr/bin/env python3
"""
This module contains functions for extracting data from multifile NetCDF
datasets, for use in conjunction with the TAMSAT alert system.
"""

import xarray as xr
import pandas as pd
from glob import glob


def _get_dataset(path):
    """
    Creates an xarray dataset from a glob expression

    :param path: A glob expression specifying the location of the data.
                 When full paths are listed, the alphanumeric order of
                 the files must match the time order
    :return: An xarray dataset
    """
    # Construct list of files to use.  These should be alphanumerically ordered
    file_list = sorted(glob(path))

    # Construct an xarray dataset with all of the files
    dataset = xr.open_mfdataset(file_list,
                                decode_times=True,
                                autoclose=True)

    # Decode CF metadata (this is quick, but creates a new dataset)
    return xr.decode_cf(dataset)


def extract_point_timeseries(path, lon, lat):
    """
    Extracts a timeseries from a set of NetCDF files at a specified location.

    :param path: A glob expression specifying the location of the data.
                 When full paths are listed, the alphanumeric order of
                 the files must match the time order
    :param lon: The longitude at which to extract a timeseries
    :param lat: The latitude at which to extract a timeseries
    :return: A pandas DataFrame containing all variables present in the NetCDF dataset
    """
    dataset = _get_dataset(path)

    # Select nearest neighbour to co-ordinate of interest, for all variables
    timeseries = dataset.sel(lat=lat, lon=lon, method='nearest')

    # Create a pandas DataFrame from the selected data
    # This is where the extraction happens
    df = timeseries.to_dataframe()

    return df


def extract_area_mean_timeseries(path, minlon, maxlon, minlat, maxlat):
    """
    Extracts a timeseries from a set of NetCDF files averaged over a specified region.

    :param path: A glob expression specifying the location of the data.
                 When full paths are listed, the alphanumeric order of
                 the files must match the time order
    :param minlat: The minimum latitude of the region over which to extract a timeseries
    :param maxlat: The maximum latitude of the region over which to extract a timeseries
    :param minlon: The minimum longitude of the region over which to extract a timeseries
    :param maxlon: The maximum longitude of the region over which to extract a timeseries
    :return: A pandas DataFrame containing all variables present in the NetCDF dataset
    """
    dataset = _get_dataset(path)

    ln = dataset.coords['lon']
    lt = dataset.coords['lat']
    # Select the region of the data
    subset = dataset.loc[dict(
        lon=ln[(ln >= minlon) & (ln <= maxlon)],
        lat=lt[(lt >= minlat) & (lt <= maxlat)])]
    # Take the mean over the lon/lat dimensions
    timeseries = subset.mean(dim=('lon', 'lat'), skipna=True)

    # Create a pandas DataFrame from the selected data
    # This is where the extraction happens
    df = timeseries.to_dataframe()

    return df
