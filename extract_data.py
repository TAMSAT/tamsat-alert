#!/usr/bin/env python3
"""
This module contains functions for extracting data from multifile NetCDF
datasets, for use in conjunction with the TAMSAT alert system.

It is currently in early stages and only contains a single function
for extracting data at a point.  It will later contain methods for
averaging over a bounding box, or potentially over a shapefile
(so that averages for an entire country can be easily extracted)
"""

import xarray as xr
import pandas as pd
from glob import glob

def extract_point_timeseries(path, lon, lat):
    """
    Extracts a timeseries from a set of NetCDF files at a specified location.

    :param path: A glob expression specifying the location of the data.
                 When full paths are listed, the alphanumeric order of
                 the files must match the time order
    :param lat: The latitude at which to extract a timeseries
    :param lon: The longitude at which to extract a timeseries
    :returns: A pandas DataFrame containing all variables present in the NetCDF dataset
    """
    # Construct list of files to use.  These should be alphanumerically ordered
    file_list = sorted(glob(path))

    # Construct an xarray dataset with all of the files
    dataset = xr.open_mfdataset(file_list,
                                decode_times=True,
                                autoclose=True)

    # Decode CF metadata (this is quick, but creates a new dataset)
    dataset = xr.decode_cf(dataset)

    # Extract nearest neighbour to co-ordinate of interest, for all variables
    timeseries = dataset.sel(lat=lat, lon=lon, method='nearest')

    # Create a pandas DataFrame from the extracted data
    df = timeseries.to_dataframe()

    return df
