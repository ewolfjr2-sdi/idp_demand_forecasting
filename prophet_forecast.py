import pandas_gbq
import pandas as pd
import itertools
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
from prophet.diagnostics import cross_validation
from prophet.diagnostics import performance_metrics
from prophet.plot import plot_cross_validation_metric
from google.oauth2 import service_account


# Function to sanitize column names for BigQuery
def sanitize_column_names(df):
    df.columns = df.columns.str.replace(r'[^a-zA-Z0-9_]', '_', regex=True)
    df.columns = df.columns.str.replace(r'__+', '_', regex=True)
    df.columns = df.columns.str.strip('_')
    return df


# Function to revert one-hot encoding
def undummy(df, prefix):
    dummy_cols = [col for col in df.columns if col.startswith(prefix)]
    df[prefix.rstrip('_')] = df[dummy_cols].idxmax(axis=1).str.replace(prefix, '')
    df.drop(columns=dummy_cols, inplace=True)
    return df


# Assign variables for GCP project and credentials
gcp_project_id = "dce-gcp-training"

credentials = service_account.Credentials.from_service_account_file(
    '.config/gcp_service_account.json',
)

# Load data from BigQuery
data = pandas_gbq.read_gbq("SELECT * FROM `dce-gcp-training.idp_demand_forecasting.model_features`", project_id=gcp_project_id, credentials=credentials)

# Convert date string to actual date datatype
data['ds'] = pd.to_datetime(data['ds'])

# Data basic info
# print('== Data Info:')
# print(data.info())
# print(data.head())

# One-hot encode categorical regressors
data = pd.get_dummies(data, columns=['distribution_center_name', 'product_name'])

# Create Prophet model
model = Prophet(
    yearly_seasonality=True,
    changepoint_prior_scale=0.1,
    seasonality_prior_scale=0.01
)

# Add regressors
for col in data.columns:
    if col.startswith('distribution_center_name_') or col.startswith('product_name_'):
        model.add_regressor(col)

# Fit model
model.fit(data)

# Make future dates DataFrame for forecasting
future = model.make_future_dataframe(periods=30, freq='1D')  # Adjust forecast period as needed

# Identify the one-hot encoded columns
regressor_columns = [col for col in data.columns if col.startswith('distribution_center_name_') or col.startswith('product_name_')]

# Get the last known values of the regressors
last_known_values = data.iloc[-1][regressor_columns]

# Add regressors to the future dataframe
future = future.merge(data[['ds'] + regressor_columns], on='ds', how='left')

# Fill NaN values with the last known values
future[regressor_columns] = future[regressor_columns].fillna(last_known_values)

# Check future dataframe output
# print('== Future Dataframe')
# print(future.info())
# print(future.head())

# Generate forecast for future dates
forecast = model.predict(future)

# model.plot_components(forecast)

# Merge one-hot encoded regressor columns from future into forecast based on 'ds'
forecast = forecast.merge(future[['ds'] + regressor_columns], on='ds', how='left')

# Undummy 'distribution_center_name'
forecast = undummy(forecast, 'distribution_center_name_')

# Undummy 'product_name'
forecast = undummy(forecast, 'product_name_')

forecast = forecast[['ds', 'distribution_center_name', 'product_name', 'yhat', 'yhat_lower', 'yhat_upper']]

# Check the results
# print(forecast.head())

# Fill NaN values in regressor columns with the last known values
# for col in regressor_columns:
#     if col in last_known_values:
#         forecast[col].fillna(last_known_values[col], inplace=True)

# Check forecast dataframe output
# print('== Forecast Dataframe:')
# print(forecast.info())
# print(forecast.tail())

# Perform cross-validation for the current distribution center
# cv_results = cross_validation(model, initial='730 days', period='90 days', horizon='30 days')

# Print cv results
# print("== Cross-validation Results:")
# print(cv_results)

# Visualize results
# plot_cross_validation_metric(cv_results, metric='mae')
# plt.show()

# Calculate error metrics for all cross-validation results
# metrics = performance_metrics(cv_results)

# Print error metrics
# print("== Performance Metrics:")
# print(metrics)

# Output forecast data to a CSV file
# forecast_data.to_csv('forecast_results.csv', index=False)

########## Push results to BigQuery ##########

# Forecast results
# pandas_gbq.to_gbq(
#     sanitize_column_names(forecast).reset_index().drop(columns='index'),
#     'dce-gcp-training.idp_demand_forecasting.prophet_model_forecast_results',
#     project_id=gcp_project_id,
#     if_exists='replace',
#     credentials=credentials
# )

# # Model metrics
# Push model metrics to BigQuery
# metrics['horizon'] = metrics['horizon'].astype(str)
# pandas_gbq.to_gbq(
#     metrics,
#     'dce-gcp-training.idp_demand_forecasting.prophet_model_metrics',
#     project_id=gcp_project_id,
#     if_exists='replace',
#     credentials=credentials
# )


