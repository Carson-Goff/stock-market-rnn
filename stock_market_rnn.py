# -*- coding: utf-8 -*-
"""stock-market-rnn.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1e1co4eAD8q8uu_UdkzFyYpOGZBnHhqqu
"""

import pandas as pd
from pandas.tseries.offsets import DateOffset
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from multiprocessing import Pool

def load_data(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        ticker = os.path.basename(file_path).split('.')[0]
        df['Ticker'] = ticker
        return df
    else:
        raise FileNotFoundError(f"No data file found at the specified path: {file_path}")

file_path = '/content/drive/MyDrive/data/stocks/AAPL.csv'
stock_data = load_data(file_path)
stock_data['Date'] = pd.to_datetime(stock_data['Date'], errors='coerce')
stock_data.sort_values(by='Date', inplace=True)

print(stock_data.info())
print(stock_data.describe())
print(stock_data.isnull().sum())

def plot_single_ticker(data, ticker='AAPL'):
    ticker_data = data[data['Ticker'] == ticker]

    if ticker_data.empty:
        print(f"No data available for ticker: {ticker}")
        return

    plt.figure(figsize=(14, 7))
    plt.plot(ticker_data['Date'], ticker_data['Adj Close'], label='Adj Close')
    plt.title(f'Adjusted Stonk Price Over Time for {ticker}')
    plt.xlabel('Date')
    plt.ylabel('Adjusted Close Price')
    plt.legend()
    plt.grid(True)
    plt.show()

plot_single_ticker(stock_data, 'AAPL')

def create_sequences(prices, window_size):
    X, y = [], []
    for i in range(len(prices) - window_size):
        X.append(prices[i:(i + window_size)])
        y.append(prices[i + window_size])
    return np.array(X), np.array(y)

# Function to load and process stock data from a file
def load_and_process_stock(filepath, window_size=20):
    data = pd.read_csv(filepath)
    data['Date'] = pd.to_datetime(data['Date'])
    data.sort_values('Date', inplace=True)
    data.dropna(subset=['Adj Close'], inplace=True)
    return create_sequences(data['Adj Close'].values, window_size)

# Function to build the LSTM model
def build_model(input_shape):
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dense(25),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

file_path = '/content/drive/MyDrive/data/stocks/AAPL.csv'
window_size = 20
X, y = load_and_process_stock(file_path, window_size)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

model = build_model((window_size, 1))
history = model.fit(X_train, y_train, epochs=50, batch_size=64, validation_split=0.1)

loss, val_loss = history.history['loss'], history.history['val_loss']
print(f"Training Loss: {loss[-1]}")
print(f"Validation Loss: {val_loss[-1]}")

# model.save('stocks_rnn.h5')

# model = load_model('stocks_rnn.h5')

predictions = model.predict(X_test)

# Handle potential NaNs in predictions and y_test
predictions = np.nan_to_num(predictions, nan=np.nanmean(predictions))
y_test = np.nan_to_num(y_test, nan=np.nanmean(y_test))

# Calculate Mean Squared Error
try:
    mse = mean_squared_error(y_test, predictions)
    print(f"Mean Squared Error: {mse}")
except ValueError as e:
    print("Error calculating MSE:", e)

# Plot results
plt.figure(figsize=(14, 5))
plt.plot(y_test, label='True Value')
plt.plot(predictions, label='Predicted Value')
plt.title('Stock Price Prediction')
plt.xlabel('Time Steps')
plt.ylabel('Normalized Price')
plt.legend()
plt.grid(True)
plt.show()

def forecast_future_prices(data, ticker='AAPL', model=None, days_ahead=90, window_size=20):
    # Extract data for the specified ticker
    ticker_data = data[data['Ticker'] == ticker]
    if ticker_data.empty:
        print(f"No data available for ticker: {ticker}")
        return

    # Handle NaNs in the data
    last_points = ticker_data['Adj Close'].tail(window_size).values
    if np.isnan(last_points).any():
        print("NaN values found in input data, replacing with column mean")
        column_mean = np.nanmean(last_points)
        last_points = np.nan_to_num(last_points, nan=column_mean)

    # Prepare data for forecasting
    last_points = last_points.reshape(1, -1)
    last_date = ticker_data['Date'].iloc[-1]
    future_dates = pd.date_range(start=last_date, periods=days_ahead + 1, freq='B')[1:]
    forecasted_prices = np.array([])

    # Generate forecasts
    for i in range(days_ahead):
        daily_forecast = model.predict(last_points).flatten()
        forecasted_prices = np.append(forecasted_prices, daily_forecast)
        last_points = np.append(last_points.flatten()[1:], daily_forecast).reshape(1, -1)

    # Handling NaNs in forecasted prices
    if np.isnan(forecasted_prices).any():
        forecasted_mean = np.nanmean(forecasted_prices)
        forecasted_prices = np.nan_to_num(forecasted_prices, nan=forecasted_mean)

    # Filter data for the years 2019 to 2021
    start_date = pd.Timestamp('2019-01-01')
    end_date = pd.Timestamp('2021-12-31')
    filtered_data = ticker_data[(ticker_data['Date'] >= start_date) & (ticker_data['Date'] <= end_date)]

    # Plotting
    plt.figure(figsize=(14, 7))
    plt.plot(filtered_data['Date'], filtered_data['Adj Close'], label='Historical Adj Close')
    plt.plot(future_dates, forecasted_prices, linestyle='--', label='Forecasted Adj Close')
    plt.title(f'Forecast of Adjusted Close Price for {ticker} Over Next {days_ahead} Days')
    plt.xlabel('Date')
    plt.ylabel('Adjusted Close Price')
    plt.xlim([start_date, future_dates[-1]])  # Adjust x-axis limits to show specific range
    plt.legend()
    plt.grid(True)
    plt.show()

# Usage example assuming 'model' and 'scaler' are already defined and fit
forecast_future_prices(stock_data, 'AAPL', model=model, days_ahead=90, window_size=20)