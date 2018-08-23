#!/usr/bin/env python3

from tamsat_alert import *


#The following parameters will be modified by the user
init_year=2010
init_month = 12
init_day = 1

periodstart_year = 2010 #Menu name should be 'Run start year'. The date init_year,init_month,init_day should fall within period_start_year,period_start_month,period_start_day to period_end_year, period_end_month, period_end_day
periodstart_month = 1 #Menu name should be 'Run start month'
periodstart_day = 1 #Menu name should be 'Run start day'
periodend_year = 2012 #Menu name should be 'Run end year'
periodend_month = 12 #Menu name should be 'Run end month'
periodend_day = 31 #Menu name should be 'Run end day'

forcintereststart_month = 1 #Menu name should be 'Meteorological forecast period start month'
forcintereststart_day = 1 #Menu name should be 'Meteorological forecast period start day'
forcinterestend_month = 9 #Menu name should be 'Meteorological forecast period end month'
forcinterestend_day = 30 #Menu name should be 'Meteorological forecast period end day'

#These parameters represent the start and end of the period of interest
intereststart_month = 11 #Menu name should be 'Period of interest start month'
intereststart_day = 1 #Menu name should be 'Period of interest start day'
interestend_month = 2 #Menu name should be 'Period of interest end month'
interestend_day = 28 #Menu name should be 'Period of interest end day'


stat = 'normal'#Menu name should be 'Probability distribution for percentile calculations'. Possible values are 'normal'and 'ecdf'
sta_name = "Tamale" #This is the title of the plot, the user can specify any name
weights = [0,0,1]  #Menu name should be 'Meteorological forecast tercile probabilities'

#In addition the user can specify these values, but they will need to be modified to be more intuitive

rainfallcolumn = 3 #Menu name should be 'Risk assessment metric variable'. Possible values 1 -> 10
calccumulative = 1 #Menu name should be ''Cumulative or mean risk assessment metric variable'. Possible values are 1 for cumulative, 0 for mean

#The following variables should be determined by the back end
filename = 'all_hist.txt' #This will be replaced by the data extraction script
leapremoved = 0
#These dates are the start and end of the input data. The initiation day should fall within this period. It is assumed that the data start on January 1st and end on December 31st.
datastartyear=1970
dataendyear =2011

#These parameters represent the start and end of the climatological period, and are used for the calculation of percentiles
climstartyear = 1970
climendyear = 2009

leapinit = True
climatological_metric_file = "histmetric.txt"
forecast_metric_file = "forecastmetric.txt"
ensemble_metric_file = "ensemble.txt"



intereststart_year = 1970 #For historical time series. Generally this is the same as the climatology.
interestend_year = 2009 #For historical time series. Generally this is the same as the climatology

init_date = dt.date(init_year, init_month, init_day)
#tamsat_alert(filename, 'rfe', init_date)

tamsat_alert(filename, leapremoved, datastartyear, dataendyear, init_year, init_month, init_day, periodstart_year, periodstart_month, periodstart_day, periodend_year, periodend_month, periodend_day, climstartyear, climendyear, leapinit, climatological_metric_file, forecast_metric_file, ensemble_metric_file,intereststart_month, intereststart_day, interestend_month, interestend_day, intereststart_year, interestend_year, rainfallcolumn, calccumulative, forcintereststart_month, forcintereststart_day, forcinterestend_month, forcinterestend_day, stat,sta_name, weights, './')
