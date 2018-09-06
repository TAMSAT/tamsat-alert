import numpy as np
import pandas as pd
import datetime as dt
from collections import OrderedDict
from .tamsat_alert_plots import risk_prob_plot
from .extract_data import extract_timeseries


def tamsat_alert(data_path, lat, lon, cast_date,
                 run_start, run_end,
                 # Hopefully ditch these and use data bounds
                 climstartyear, climendyear,

                 # These are required, but could do with a better name
                 intereststart_month, intereststart_day, interestend_month, interestend_day,

                 # Hopefully ditch these and use data bounds
                 intereststart_year, interestend_year,

                 # Required, move it down though
                 cumulative_not_mean,

                 # These are required, give them a better name
                 forcintereststart_month, forcintereststart_day, forcinterestend_month, forcinterestend_day,

                 # Type of statistic to use in the plot
                 norm_not_ecdf,

                 # This is the plot title.  TODO - Default/fixed value for it
                 sta_name,

                 # Need to document this better
                 weights,

                # Move up the list?
                output_dir):
    '''
    Generates the data and plots for TAMSAT Alert.  Currently a work-in-progress.
    The method signature will change in the near future, so not currently documented

    :param data_path:   The path to the TAMSAT rainfall data
    :param lat:         The latitude at which to extract data
    :param lon:         The longitude at which to extract data
    :param cast_date:   The date at which to start fore/hind-cast
    :param run_start:   The start date for the runs.  All ensembles will be
                        constructed from data between this date and cast_date
    :param run_start:   The end date for the runs.  All ensembles will be
                        constructed from data between cast_date and this date,
                        but for every available year in the dataset
    '''

    # Some sanity checks
    # TODO more of these
    if(cast_date < run_start or cast_date > run_end):
        raise ValueError('cast_date must fall between run_start and run_end')

    # Extract a DataFrame containing the data at the specified location
    data = extract_point_timeseries(data_path, lat, lon)

    # This can be a single value or an array
    vars_of_interest = ['rfe']

    # The start and end years to create ensemble members from
    ensemble_start_year = climstartyear
    ensemble_end_year = climendyear
    # TODO - Do we want the entire range of the dataset here?
    # ensemble_start_year = data.index[0].year
    # ensemble_end_year = data.index[-1].year
    # TODO - These can possibly be used as interest[start/end]_year
    # Otherwise we need some other way of determining the start/end year of interest

    # Select only the data we want to deal with
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
    if cumulative_not_mean:
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

    # Plot function chooses statistic type based on a string
    stat = norm_not_ecdf ? 'norm' : 'ecdf'

    risk_prob_plot(climstartyear, climendyear, datastartyear, dataendyear,          init_year, init_month, init_day, stat, sta_name, weights, climatological_sums, ensemble_totals, forecast_sums, output_dir)

    # Now go into output_dir and create a zip file containing everything.
    # TODO return path to the zip file?
    # TODO create a temporary output dir, pass it to risk_prob_plot, zip everything
    # based on an input parameter, then return that path?


def strip_leap_days(data):
    '''
    Removes leap days from a dataset

    :param data: A pandas DataFrame containing the data to remove leap years from
    :return: A copy of the same pandas DataFrame, with all values occurring
             on the 29th February removed
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

    :param data:                The timeseries data
    :param no_leap_data:        The timeseries data, with leap days removed
    :param cast_date:           The (fore/hind)cast date
    :param run_start:           The date to start ensemble runs
    :param run_end:             The date to end ensemble runs
    :param ensemble_start_year: The first year in the data to construct an
                                ensemble run from
    :param ensemble_end_year:   The last year in the data to construct an
                                ensemble run from
    :param retain_leaps:        If True, keeps leap days in the spinup data
                                Optional, defaults to True

    :return:                    An OrderedDict whose keys are the ensemble years
                                and whose values are pandas DataFrames containing
                                the ensemble data
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
    from the first occurrence of (start_day, start_month) to the next
    occurrence of (end_day, end_month), inclusive.

    :param members:     An OrderedDict containing ensemble years mapped to
                        pandas DataFrames with ensemble data
    :start_day:         The day of the month at which to start the sum over
    :start_month:       The month of the year at which to start the sum over
    :end_day:           The day of the month at whose first occurrence to
                        end the sum
    :end_month:         The month of the year at whose first occurrence to
                        end the sum

    :return:            A DataFrame whose index is the keys of members, and
                        whose values are the calculated sums
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
    to the end date (end_day/end_month) of that year.

    If the start-end dates cross the year boundary, the year is defined as the
    year at the start date.

    :param data_no_leaps:   A pandas DataFrame containing the data, with leap days removed
    :param start_day:       The day of the month to start operating on
    :param start_month:     The month of the year to start operating on
    :param end_day:         The day of the month to stop operating on (exclusive)
    :param end_month:       The month of the year to stop operating on (exclusive)
    :param start_year:      The first year to perform the operation on
    :param end_year:        The last year to perform the operation on.
    :param operation:       The operation to perform.  Should be a function (e.g. np.sum)

    :return:                A pandas DataFrame containing years as the index, and
                            the results of the operation as the values
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

        if(end > data_no_leaps.index[-1]):
            # In this case, the end point falls outside the data range
            # This would lead to truncated data, so we do not perform the
            # operation.  This will also be true for all following years,
            # hence we use break, rather than continue
            break

        # Subset the data to extract the desired period for the current year
        subset = data_no_leaps.loc[np.logical_and(
            data_no_leaps.index >= start,
            data_no_leaps.index < end,
        )]

        # Perform the operation (usually np.sum() or np.mean() on the subset)
        values.append(operation(subset))

    return pd.DataFrame(values, years)
