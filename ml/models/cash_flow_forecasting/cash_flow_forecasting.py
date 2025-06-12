import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

class CashFlowForecaster:
    def __init__(self):
        self.model = None
        self.model_fit = None

    def preprocess_data(self, df):
        # Ensure 'date' column is datetime and set as index
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        # Resample to monthly frequency, filling missing values with 0
        df = df['amount'].resample('M').sum().fillna(0)
        return df

    def train(self, data):
        # For simplicity, using ARIMA(1,1,1) as a starting point
        # In a real scenario, model selection and hyperparameter tuning would be performed
        order = (1, 1, 1)
        self.model = ARIMA(data, order=order)
        self.model_fit = self.model.fit()

    def predict(self, steps):
        if self.model_fit is None:
            raise ValueError("Model has not been trained yet. Call train() first.")
        forecast = self.model_fit.forecast(steps=steps)
        return forecast

if __name__ == '__main__':
    # Example Usage:
    # Create some dummy data for demonstration
    data = {
        'date': pd.to_datetime(['2023-01-15', '2023-02-10', '2023-03-05', '2023-04-20', '2023-05-12']),
        'amount': [1000, -500, 1200, -700, 1500]
    }
    df = pd.DataFrame(data)

    forecaster = CashFlowForecaster()
    processed_data = forecaster.preprocess_data(df)
    forecaster.train(processed_data)
    predictions = forecaster.predict(3)

    print("Processed Data:\n", processed_data)
    print("\nForecasted Cash Flow for next 3 months:\n", predictions)


