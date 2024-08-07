from prophet import Prophet
from prophet.plot import add_changepoints_to_plot
from sklearn.metrics import mean_absolute_error
from prophet.diagnostics import cross_validation
from prophet.diagnostics import performance_metrics
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('fivethirtyeight')

#################################################
################### LOAD DATA ###################

file = 'Bakery_Sales.csv'

df = pd.read_csv(file)

###########################################
################### EDA ###################

# Select Columns for analysis
df = df[['datetime', 'tiramisu_croissant']]

# Convert the 'Datetime' column to actual datetime objects
df['datetime'] = pd.to_datetime(df['datetime'])
df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d')
df['datetime'] = pd.to_datetime(df['datetime'])

# Drop rows with any NaN values
df = df.dropna()

# Group by day
df.groupby(df['datetime'].dt.date)

# Basic data info
print(df.info())
print(df.describe())
print(df.head())

# # Rename columns to conform to Prophet input columns. ds (the time column) and y (the metric column)
df = df.rename(columns={'datetime': 'ds',
                        'tiramisu_croissant': 'y'})
print(df.head())
#
# # Visualize the data
print('== Data Visualization')
ax = df.set_index('ds').plot(figsize=(12, 8))
ax.set_ylabel('Number of Items Sold')
ax.set_xlabel('Date')

plt.show()

########################################################
################### CREATE THE MODEL ###################

# Define holidays or special events
events = pd.DataFrame({
    'holiday': 'special_event',
    'ds': pd.to_datetime(['2024-08-15', '2024-10-15']),
    'lower_window': 0,
    'upper_window': 1,
})

# set the uncertainty interval to 95% (the Prophet default is 80%)
model = Prophet(interval_width=0.95, yearly_seasonality=True, weekly_seasonality=True)  # holidays=events)

# Add built-in country holidays
model.add_country_holidays(country_name='US')  # Replace 'US' with your desired country code

# Fit the model
model.fit(df)
#
# Create future dataframe
# We instructed Prophet to generate 36 datestamps in the future. This can be changed as needed.
# Because we are working with monthly data, we clearly specified the desired frequency of the timestamps (in this case, MS is the start of the month)
future_dates = model.make_future_dataframe(periods=36, freq='MS')
future_dates.head()

# Predict future values
forecast = model.predict(future_dates)

# Prophet returns a large DataFrame with many interesting columns, but we subset our output to the columns most relevant to forecasting. These are:
# ds: the datestamp of the forecasted value
# yhat: the forecasted value of our metric (in Statistics, yhat is a notation traditionally used to represent the predicted values of a value y)
# yhat_lower: the lower bound of our forecasts
# yhat_upper: the upper bound of our forecasts
# A variation in values from the output presented is to be expected as Prophet relies on Markov chain Monte Carlo (MCMC) methods to generate its forecasts.
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].head()

# Plot the results of our forecasts
# Prophet plots the observed values of our time series (the black dots), the forecasted values (blue line) and the uncertainty intervals of our forecasts (the blue shaded regions).
print('== Forecasted Data With Uncertainty')
model.plot(forecast, uncertainty=True)
plt.show()

##########################################################################
################### PLOTTING THE FORECASTED COMPONENTS ###################
# Plot components of the forecast
print('== Forecast Components')
model.plot_components(forecast)
plt.show()

######################################################################
################### Adding ChangePoints to Prophet ###################
# Changepoints are the datetime points where the time series have abrupt changes in the trajectory.
# By default, Prophet adds 25 changepoints to the initial 80% of the data-set.
# Let’s plot the vertical lines where the potential changepoints occurred.
print('== Plot With Default Changepoints')
fig = model.plot(forecast)
a = add_changepoints_to_plot(fig.gca(), model, forecast)
plt.show()
# Output the dates where changepoints occurred
print(f'== Changpoint Dates {model.changepoints}')

# We can change the inferred changepoint range by setting the changepoint_range
# The number of changepoints can be set by using the n_changepoints parameter when initializing prophet.
print('== Changpoints Set To 20 with yearly seasonality')
pro_change = Prophet(n_changepoints=20, yearly_seasonality=True, weekly_seasonality=True)
forecast = pro_change.fit(df).predict(future_dates)
fig = pro_change.plot(forecast);
a = add_changepoints_to_plot(fig.gca(), pro_change, forecast)
plt.show()

#######################################################
################### ADJUSTING TREND ###################
# Prophet allows us to adjust the trend in case there is an overfit or underfit.
# changepoint_prior_scale helps adjust the strength of the trend.
# Default value for changepoint_prior_scale is 0.05.
# Decrease the value to make the trend less flexible.
# Increase the value of changepoint_prior_scale to make the trend more flexible.
# Increasing the changepoint_prior_scale to 0.08 to make the trend flexible.
print('== Changpoints and Prior Scale With Best Params')
pro_change = Prophet(n_changepoints=20, yearly_seasonality=True, seasonality_prior_scale=0.01, changepoint_prior_scale=0.01)
forecast = pro_change.fit(df).predict(future_dates)
fig = pro_change.plot(forecast);
a = add_changepoints_to_plot(fig.gca(), pro_change, forecast)
plt.show()

# Decreasing the changepoint_prior_scale to 0.001 to make the trend less flexible.
# print('== Changpoints With Trend Adjustment For Less Flexibility')
# pro_change = Prophet(n_changepoints=20, yearly_seasonality=True, changepoint_prior_scale=0.001)
# forecast = pro_change.fit(df).predict(future_dates)
# fig = pro_change.plot(forecast);
# a = add_changepoints_to_plot(fig.gca(), pro_change, forecast)
# plt.show()

##############################################################################
########## Use this code below to get the best parameters for model ##########
# param_grid = {
#     'changepoint_prior_scale': [0.001, 0.01, 0.1, 0.5],
#     'seasonality_prior_scale': [0.01, 0.1, 1.0, 10.0],
# }
#
#
# # Generate all combinations of parameters
# all_params = [dict(zip(param_grid.keys(), v)) for v in itertools.product(*param_grid.values())]
# rmses = []  # Store the RMSEs for each params here
#
#
# # Use cross validation to evaluate all parameters
# for params in all_params:
#     m = Prophet(**params).fit(df)  # Fit model with given params
#     df_cv = cross_validation(m, initial='180 days', period='90 days', horizon='30 days')
#     df_p = performance_metrics(df_cv, rolling_window=1)
#     rmses.append(df_p['rmse'].values[0])
#
#
# # Find the best parameters
# tuning_results = pd.DataFrame(all_params)
# tuning_results['rmse'] = rmses
# print(tuning_results)
#
#
# best_params = all_params[np.argmin(rmses)]
# print(best_params)
