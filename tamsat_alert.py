# Required imports for numerical stuff
import numpy as np
import pandas as pd
import datetime as dt
from collections import OrderedDict
from tamsat_alert_plots import risk_prob_plot


def tamsat_alert(filename, leapremoved, datastartyear, dataendyear, init_year, init_month, init_day, periodstart_year, periodstart_month, periodstart_day, periodend_year, periodend_month, periodend_day, climstartyear, climendyear, leapinit, climatological_metric_file, forecast_metric_file, ensemble_metric_file, intereststart_month, intereststart_day, interestend_month, interestend_day, intereststart_year, interestend_year, rainfallcolumn, calccumulative, forcintereststart_month, forcintereststart_day, forcinterestend_month, forcinterestend_day, stat, sta_name, weights, outdir):
    '''
    Generates the data and plots for TAMSAT Alert.  Currently a work-in-progress.
    The method signature will change in the near future, so not currently documented
    '''

    # Setup variables temporarily.
    # These will be replaced by args when we have the full code,
    # and the function signature is finalised

    # This can be a single value or an array
    vars_of_interest = ['rfe']
    # The date of the forecast / hindcast
    cast_date = dt.date(init_year, init_month, init_day)
    # The start and end dates for the run - these define the ensembles.
    # The cast_date should be between these dates TODO - sanity check
    run_start = dt.date(periodstart_year, periodstart_month, periodstart_day)
    run_end = dt.date(periodend_year, periodend_month, periodend_day)
    # The start and end years to create ensemble members from
    ensemble_start_year = climstartyear
    ensemble_end_year = climendyear

    # All this code will go - it will be extracted from the data files
    # using Ross's extraction code
    raw_data = np.genfromtxt(filename)
    # Data is defined to always start on the 1st January
    current_date = dt.date(datastartyear, 1, 1)
    # Create array of dates
    dates = np.empty(raw_data.shape[0], dt.date)
    for i in np.arange(len(dates)):
        dates[i] = current_date
        current_date += dt.timedelta(days=1)
    data = pd.DataFrame(raw_data, dates,
                        columns=['col1', 'col2', 'rfe', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9', 'col10'])

    # TODO some sanity checks on various input parameters:

    # Select the data we want to deal with
    data = data[vars_of_interest]

    # Remove leap years from data
    # This is so that when we construct ensemble members from historical runs,
    # they will all be guaranteed to have the same length.
    #
    # If there are already no leap years in the data, this will return an identical
    # pandas dataframe
    data_no_leaps = strip_leap_days(data)

    # Initialise the ensemble members.  This returns an OrderedDict mapping
    # ensemble member years (as ints) to the data
    ensemble_members = init_ensemble_data(
        data, data_no_leaps, cast_date, run_start,
        run_end, ensemble_start_year, ensemble_end_year)

    # Sum the ensemble members.  This returns a DataFrame with ensemble
    # years as the index, and the variables of interest as the columns.
    # Values are the sums of the ensemble members over the FIRST occurrence
    # of the period of interest date range
    ensemble_totals = sum_ensemble_members(
        ensemble_members, intereststart_day, intereststart_month,
        interestend_day, interestend_month)

    # Pick which operation to perform on the ensemble members
    if calccumulative:
        operation = np.sum
    else:
        operation = np.mean

    # Calculate the timeseries for the two desired periods
    climatological_sums = ensemble_timeseries(data_no_leaps,
                                        intereststart_day,
                                        intereststart_month,
                                        interestend_day,
                                        interestend_month,
                                        intereststart_year,
                                        interestend_year,
                                        operation)

    forecast_sums = ensemble_timeseries(data_no_leaps,
                                        forcintereststart_day,
                                        forcintereststart_month,
                                        forcinterestend_day,
                                        forcinterestend_month,
                                        intereststart_year,
                                        interestend_year,
                                        operation)

    # This has been only very slightly modified from its original state
    # It now takes the DataFrames rather than filenames, but is otherwise
    # the same as in the old version.

    # TODO The old version possibly had the last 3 arguments in the wrong order
    # Check what order they're supposed to be in
    risk_prob_plot(climstartyear, climendyear, datastartyear, dataendyear,          init_year, init_month, init_day, stat, sta_name, weights, climatological_sums, ensemble_totals, forecast_sums, outdir)


def strip_leap_days(data):
    '''
    Takes a pandas DataFrame whose index is a datetime.date, and return a
    copy of the DataFrame, with any rows which fall on February 29th removed.
    This guarantees that all years have the same length.
    '''
    stripped_data = data.drop(
        [date for date in data.index
            if (date.month == 2 and date.day == 29)])

    return stripped_data


def init_ensemble_data(data, no_leap_data, cast_date, run_start, run_end, ensemble_start_year, ensemble_end_year, retain_leaps=True):
    '''
    Takes the data and extracts ensemble members for each year.

    Each ensemble member consists of:

    * The SAME spinup data which is data from the period from run_start to cast_date
    * The data from the cast_date of the ensemble year, up to the run_end date of
            the ensemble year.

    i.e. It is a bunch of timeseries which start the same, but then vary going forward
    from the (fore/hind)cast date
    '''

    spinupdata = data if retain_leaps else no_leap_data
    spinup = spinupdata.loc[np.logical_and(
        spinupdata.index >= run_start, spinupdata.index < cast_date)]

    # Return an ordered dictionary of ensemble members (i.e. years) to pandas dataframes
    ret = OrderedDict()

    # Calculate number of days to run after cast date
    n_days = (run_end - cast_date).days

    for year in np.arange(ensemble_start_year, ensemble_end_year + 1):
        # For every ensemble year, take subset of no leap data FROM:
        # The cast date in ensemble year
        # TO
        # The run_end date in ensemble year

        start_date = dt.date(year, cast_date.month, cast_date.day)
        end_date = start_date + dt.timedelta(days=n_days)
        ensemble_range = np.logical_and(
            no_leap_data.index >= start_date,
            no_leap_data.index <  end_date
        )
        ret[year] = pd.concat([spinup, no_leap_data.loc[ensemble_range]])
    return ret


def sum_ensemble_members(members, start_day, start_month, end_day, end_month):
    '''
    Calculates the sum of the values in each ensemble member ranging
    from the first occurrence of (start_day, start_month) to the next occurrence
    of (end_day, end_month), inclusive.

    Returns an OrderedDict mapping ensemble members to the appropriate sum
    '''

    values = []
    for member in members:
        data = members[member]

        # Calculate the indices within this dataframe to sum over
        start_index = 0
        end_index = 0
        # We want the first date matching the start day & month
        for i, date in enumerate(data.index):
            if(date.month == start_month and date.day == start_day):
                start_index = i
                break
        # We want the next date matching the end day & month,
        # hence we slice the data from the start_index
        for i, date in enumerate(data.index[start_index:]):
            if(date.month == end_month and date.day == end_day):
                # We need to add the start_index to i,
                # since enumerate() will start the index from 0
                end_index = i + start_index
                break

        # Now slice the data between the desired indices, and sum
        values.append(data[start_index : end_index].sum())
    return pd.DataFrame(values, members)


def ensemble_timeseries(data_no_leaps, start_day, start_month, end_day, end_month, start_year, end_year, operation):
    '''
    For each year between start_year and end_year, performs the operation
    on data ranging from the start date (start_day/start_month),
    to the end date (end_day/end_month) of the year.

    Note that we could have used start_date and end_date, but this would imply
    that ALL dates in that range were operated on.
    '''

    # This should be a leap year, to ensure we will have a valid date
    # Otherwise it is completely arbitrary, and only used to check
    # whether the range spans the year boundary.
    arbitrary_year = 2000

    # Detect whether the desired period crosses a year
    start_date = dt.date(
        arbitrary_year, start_month, start_day)
    end_date = dt.date(
        arbitrary_year, end_month, end_day)
    crosses_year = start_date > end_date

    if(crosses_year):
        years = np.arange(start_year, end_year)
    else:
        years = np.arange(start_year, end_year + 1)

    values = []
    for year in years:
        start = dt.date(year, start_month, start_day)

        # We need to increment the year if the dates cross the year boundary
        before_end_year = year
        if crosses_year:
            before_end_year = year + 1
        end = dt.date(
            before_end_year, end_month, end_day)

        # Subset the data to extract the desired period for the current year
        subset = data_no_leaps.loc[np.logical_and(
            data_no_leaps.index >= start,
            data_no_leaps.index < end,
        )]

        # Perform the operation (usually np.sum() or np.mean() on the subset)
        values.append(operation(subset))

    return pd.DataFrame(values, years)
