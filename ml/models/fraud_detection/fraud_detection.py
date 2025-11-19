import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report


class FraudDetector:
    def __init__(self):
        self.model = None

    def preprocess_data(self, df):
        # Example preprocessing: handle missing values, scale numerical features
        # In a real application, more robust feature engineering and scaling would be applied
        df = df.fillna(df.mean(numeric_only=True))
        return df

    def train(self, X):
        # Isolation Forest is an unsupervised anomaly detection algorithm
        # It works well for fraud detection where fraudulent transactions are anomalies
        self.model = IsolationForest(random_state=42)
        self.model.fit(X)

    def predict(self, X_new):
        if self.model is None:
            raise ValueError("Model has not been trained yet. Call train() first.")
        # Predict -1 for outliers (fraud), 1 for inliers (legitimate)
        return self.model.predict(X_new)

    def evaluate(self, X, y_true):
        if self.model is None:
            raise ValueError("Model has not been trained yet. Call train() first.")
        y_pred = self.model.predict(X)
        # Convert Isolation Forest output (-1, 1) to (0, 1) for classification report
        y_pred_binary = [1 if p == -1 else 0 for p in y_pred]
        y_true_binary = [
            1 if t == 1 else 0 for t in y_true
        ]  # Assuming 1 is fraud, 0 is legitimate
        print("\nFraud Detection Model Performance:")
        print(
            classification_report(
                y_true_binary, y_pred_binary, target_names=["Legitimate", "Fraud"]
            )
        )


if __name__ == "__main__":
    # Example Usage:
    # Create some dummy data for demonstration
    # 'is_fraud' column is for evaluation purposes only, Isolation Forest is unsupervised
    data = {
        "transaction_amount": [100, 200, 50, 1000, 150, 300, 5000, 75, 250, 80],
        "transaction_frequency_24h": [5, 3, 8, 1, 6, 4, 0, 7, 2, 9],
        "location_change": [
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
        ],  # 1 if location changed significantly
        "is_fraud": [0, 0, 0, 1, 0, 0, 1, 0, 0, 0],  # 0: legitimate, 1: fraud
    }
    df = pd.DataFrame(data)

    detector = FraudDetector()
    processed_df = detector.preprocess_data(df.copy())

    X = processed_df.drop("is_fraud", axis=1)
    y = processed_df["is_fraud"]

    # Train the model (unsupervised, so 'y' is not used in training)
    detector.train(X)

    # Predict on the same data for demonstration
    predictions = detector.predict(X)
    print("\nPredictions (-1 for fraud, 1 for legitimate):", predictions)

    # Evaluate the model (requires true labels)
    detector.evaluate(X, y)

    # Example of new transaction for prediction
    new_transaction = pd.DataFrame(
        {
            "transaction_amount": [6000],
            "transaction_frequency_24h": [0],
            "location_change": [1],
        }
    )
    processed_new_transaction = detector.preprocess_data(new_transaction)
    fraud_prediction = detector.predict(processed_new_transaction)
    print(f"\nPrediction for new transaction: {fraud_prediction[0]} (-1 means fraud)")
