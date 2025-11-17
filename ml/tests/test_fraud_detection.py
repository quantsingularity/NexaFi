import unittest

import pandas as pd

from NexaFi.ml.models.fraud_detection.fraud_detection import FraudDetector


class TestFraudDetector(unittest.TestCase):
    def setUp(self):
        self.detector = FraudDetector()
        self.data = {
            "transaction_amount": [100, 200, 50, 1000, 150, 300, 5000, 75, 250, 80],
            "transaction_frequency_24h": [5, 3, 8, 1, 6, 4, 0, 7, 2, 9],
            "location_change": [0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
            "is_fraud": [0, 0, 0, 1, 0, 0, 1, 0, 0, 0],  # 0: legitimate, 1: fraud
        }
        self.df = pd.DataFrame(self.data)
        self.processed_df = self.detector.preprocess_data(self.df.copy())
        self.X = self.processed_df.drop("is_fraud", axis=1)
        self.y = self.processed_df["is_fraud"]

    def test_preprocess_data(self):
        processed_df = self.detector.preprocess_data(self.df.copy())
        self.assertFalse(processed_df.isnull().any().any())

    def test_train_and_predict(self):
        self.detector.train(self.X)
        predictions = self.detector.predict(self.X)
        self.assertEqual(len(predictions), len(self.X))
        self.assertIn(-1, predictions)  # Should predict some anomalies
        self.assertIn(1, predictions)  # Should predict some legitimate transactions

    def test_evaluate(self):
        self.detector.train(self.X)
        # Redirect stdout to capture print statements from evaluate
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            self.detector.evaluate(self.X, self.y)
        output = f.getvalue()
        self.assertIn("Fraud Detection Model Performance", output)
        self.assertIn("Legitimate", output)
        self.assertIn("Fraud", output)

    def test_predict_before_train(self):
        with self.assertRaises(ValueError):
            self.detector.predict(self.X.iloc[:1])


if __name__ == "__main__":
    unittest.main()
