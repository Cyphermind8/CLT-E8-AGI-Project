# Chunk 11: AI-Based Stock Market Prediction (Linear Regression)

import numpy as np

class LinearRegression:
    """A simple linear regression model for predicting numerical values."""
    def __init__(self):
        self.slope = 0
        self.intercept = 0

    def train(self, X, y):
        """Train the model using the least squares method."""
        X_mean = np.mean(X)
        y_mean = np.mean(y)
        self.slope = np.sum((X - X_mean) * (y - y_mean)) / np.sum((X - X_mean) ** 2)
        self.intercept = y_mean - self.slope * X_mean

    def predict(self, X):
        """Make predictions using the trained model."""
        return self.slope * X + self.intercept

def stock_prediction_example():
    """Example of predicting stock prices using linear regression."""
    X = np.array([1, 2, 3, 4, 5])  # Days
    y = np.array([100, 105, 110, 120, 125])  # Stock prices

    model = LinearRegression()
    model.train(X, y)

    future_day = 6
    predicted_price = model.predict(future_day)
    print(f"Predicted stock price on day {future_day}: {predicted_price}")

# Example usage
stock_prediction_example()
