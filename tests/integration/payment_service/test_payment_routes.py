
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from NexaFi.backend.payment_service.src.main import app
from NexaFi.backend.payment_service.src.models.user import (
    ExchangeRate, PaymentMethod, RecurringPayment, Transaction, Wallet,
    WalletBalanceHistory, db)


@pytest.fixture(scope=\'module\')
def client():
    app.config[\\'TESTING\\'] = True
    app.config[\\'SQLALCHEMY_DATABASE_URI\\'] = \\'sqlite:///:memory:\\'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture(autouse=True)
def run_around_tests(client):
    with app.app_context():
        PaymentMethod.query.delete()
        Transaction.query.delete()
        Wallet.query.delete()
        WalletBalanceHistory.query.delete()
        RecurringPayment.query.delete()
        ExchangeRate.query.delete()
        db.session.commit()
    yield

def create_test_payment_method(user_id, type, provider, details, is_default=False):
    pm = PaymentMethod(
        user_id=user_id,
        type=type,
        provider=provider,
        details=details,
        is_default=is_default
    )
    db.session.add(pm)
    db.session.commit()
    return pm

def create_test_wallet(user_id, currency, balance=Decimal(\'0\')):
    wallet = Wallet(
        user_id=user_id,
        currency=currency,
        balance=balance,
        available_balance=balance,
        pending_balance=Decimal(\'0\'),
        reserved_balance=Decimal(\'0\')
    )
    db.session.add(wallet)
    db.session.commit()
    return wallet

class TestPaymentMethodRoutes:

    def test_get_payment_methods_empty(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_1\\'}
        response = client.get(
            \\'/api/v1/payment-methods\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'payment_methods\\'] == []
        assert json_data[\\'total\\'] == 0

    def test_create_payment_method_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_1\\'}
        data = {
            \\'type\\': \\'card\\',
            \\'provider\\': \\'Stripe\\',
            \\'details\\': {\\'last4\\': \\'4242\\', \\'brand\\': \\'Visa\\'}
        }
        response = client.post(
            \\'/api/v1/payment-methods\\',
            headers=headers,
            json=data
        )
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data[\\'message\\'] == \\'Payment method created successfully\\'
        assert json_data[\\'payment_method\\'][\\'type\\'] == \\'card\\'

        with app.app_context():
            pm = PaymentMethod.query.filter_by(user_id=\\'test_user_1\\', type=\\'card\\').first()
            assert pm is not None

    def test_create_payment_method_invalid_type(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_1\\'}
        data = {
            \\'type\\': \\'invalid_type\\',
            \\'provider\\': \\'Stripe\\',
            \\'details\\': {\\'last4\\': \\'4242\\', \\'brand\\': \\'Visa\\'}
        }
        response = client.post(
            \\'/api/v1/payment-methods\\',
            headers=headers,
            json=data
        )
        assert response.status_code == 400
        assert \\'Invalid payment method type.\\' in response.get_json()[\\'error\\']

    def test_get_payment_method_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_2\\'}
        pm = create_test_payment_method(
            \\'test_user_2\\',
            \\'bank_account\\',
            \\'Plaid\\',
            {\\'bank_name\\': \\'Bank of America\\', \\'account_type\\': \\'checking\\'}
        )

        response = client.get(
            f\\'/api/v1/payment-methods/{pm.id}\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'payment_method\\'][\\'type\\'] == \\'bank_account\\'

    def test_get_payment_method_not_found(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_2\\'}
        response = client.get(
            \\'/api/v1/payment-methods/non_existent_id\\',
            headers=headers
        )
        assert response.status_code == 404
        assert response.get_json()[\\'error\\'] == \\'Payment method not found\\'

    def test_update_payment_method_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_3\\'}
        pm = create_test_payment_method(
            \\'test_user_3\\',
            \\'card\\',
            \\'Stripe\\',
            {\\'last4\\': \\'1111\\', \\'brand\\': \\'Visa\\'}
        )

        data = {\\'is_default\\': True, \\'details\\': {\\'last4\\': \\'1111\\', \\'brand\\': \\'Visa\\', \\'exp_month\\': 12}}
        response = client.put(
            f\\'/api/v1/payment-methods/{pm.id}\\',
            headers=headers,
            json=data
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'message\\'] == \\'Payment method updated successfully\\'
        assert json_data[\\'payment_method\\'][\\'is_default\\'] == True

        with app.app_context():
            updated_pm = PaymentMethod.query.get(pm.id)
            assert updated_pm.is_default == True

    def test_delete_payment_method_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_4\\'}
        pm = create_test_payment_method(
            \\'test_user_4\\',
            \\'card\\',
            \\'Stripe\\',
            {\\'last4\\': \\'2222\\', \\'brand\\': \\'Mastercard\\'}
        )

        response = client.delete(
            f\\'/api/v1/payment-methods/{pm.id}\\',
            headers=headers
        )
        assert response.status_code == 200
        assert response.get_json()[\\'message\\'] == \\'Payment method deleted successfully\\'

        with app.app_context():
            deleted_pm = PaymentMethod.query.get(pm.id)
            assert deleted_pm.is_active == False

class TestTransactionRoutes:

    def test_get_transactions_empty(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_5\\'}
        response = client.get(
            \\'/api/v1/transactions\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'transactions\\'] == []
        assert json_data[\\'pagination\\'][\\'total\\'] == 0

    def test_create_payment_transaction_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_6\\'}
        pm = create_test_payment_method(
            \\'test_user_6\\',
            \\'card\\',
            \\'Stripe\\',
            {\\'last4\\': \\'3333\\', \\'brand\\': \\'Visa\\'}
        )

        data = {
            \\'amount\\': 100.00,
            \\'transaction_type\\': \\'payment\\',
            \\'payment_method_id\\': pm.id,
            \\'currency\\': \\'USD\\',
            \\'description\\': \\'Test Payment\\'}
        response = client.post(
            \\'/api/v1/transactions\\',
            headers=headers,
            json=data
        )
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data[\\'message\\'] == \\'Transaction created successfully\\'
        assert json_data[\\'transaction\\'][\\'status\\'] == \\'completed\\'
        assert json_data[\\'transaction\\'][\\'amount\\'] == 100.00

        with app.app_context():
            transaction = Transaction.query.filter_by(user_id=\\'test_user_6\\').first()
            assert transaction is not None
            wallet = Wallet.query.filter_by(user_id=\\'test_user_6\\', currency=\\'USD\\').first()
            assert wallet.balance > Decimal(\'0\')

    def test_create_withdrawal_transaction_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_7\\'}
        wallet = create_test_wallet(\'test_user_7\', \'USD\', Decimal(\'500.00\'))

        data = {
            \\'amount\\': 50.00,
            \\'transaction_type\\': \\'withdrawal\\',
            \\'currency\\': \\'USD\\',
            \\'description\\': \\'Test Withdrawal\\'}
        response = client.post(
            \\'/api/v1/transactions\\',
            headers=headers,
            json=data
        )
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data[\\'message\\'] == \\'Transaction created successfully\\'
        assert json_data[\\'transaction\\'][\\'status\\'] == \\'completed\\'

        with app.app_context():
            updated_wallet = Wallet.query.get(wallet.id)
            assert updated_wallet.balance == Decimal(\'450.00\')

    def test_create_withdrawal_insufficient_balance(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_8\\'}
        wallet = create_test_wallet(\'test_user_8\', \'USD\', Decimal(\'10.00\'))

        data = {
            \\'amount\\': 50.00,
            \\'transaction_type\\': \\'withdrawal\\',
            \\'currency\\': \\'USD\\',
            \\'description\\': \\'Test Withdrawal\\'}
        response = client.post(
            \\'/api/v1/transactions\\',
            headers=headers,
            json=data
        )
        assert response.status_code == 400
        assert response.get_json()[\\'error\\'] == \\'Insufficient balance\\'

    def test_get_transaction_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_9\\'}
        transaction = Transaction(
            user_id=\'test_user_9\',
            transaction_type=\'deposit\',
            amount=Decimal(\'200.00\'),
            currency=\'USD\',
            status=\'completed\'
        )
        with app.app_context():
            db.session.add(transaction)
            db.session.commit()
            transaction_id = transaction.id

        response = client.get(
            f\\'/api/v1/transactions/{transaction_id}\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'transaction\\'][\\'amount\\'] == 200.00

    def test_get_transaction_not_found(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_9\\'}
        response = client.get(
            \\'/api/v1/transactions/non_existent_id\\',
            headers=headers
        )
        assert response.status_code == 404
        assert response.get_json()[\\'error\\'] == \\'Transaction not found\\'

class TestWalletRoutes:

    def test_get_wallets_empty(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_10\\'}
        response = client.get(
            \\'/api/v1/wallets\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'wallets\\'] == []
        assert json_data[\\'total\\'] == 0

    def test_get_wallet_by_currency_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_11\\'}
        wallet = create_test_wallet(\'test_user_11\', \'EUR\', Decimal(\'1000.00\'))

        response = client.get(
            \\'/api/v1/wallets/EUR\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'wallet\\'][\\'currency\\'] == \\'EUR\\'
        assert json_data[\\'wallet\\'][\\'balance\\'] == 1000.00

    def test_get_wallet_by_currency_create_new(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_12\\'}
        response = client.get(
            \\'/api/v1/wallets/JPY\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'wallet\\'][\\'currency\\'] == \\'JPY\\'
        assert json_data[\\'wallet\\'][\\'balance\\'] == 0.00

        with app.app_context():
            wallet = Wallet.query.filter_by(user_id=\\'test_user_12\\', currency=\\'JPY\\').first()
            assert wallet is not None

class TestRecurringPaymentRoutes:

    def test_get_recurring_payments_empty(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_13\\'}
        response = client.get(
            \\'/api/v1/recurring-payments\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'recurring_payments\\'] == []
        assert json_data[\\'total\\'] == 0

    def test_create_recurring_payment_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_14\\'}
        pm = create_test_payment_method(
            \\'test_user_14\\',
            \\'card\\',
            \\'Visa\\',
            {\\'last4\\': \\'5555\\'}
        )

        data = {
            \\'payment_method_id\\': pm.id,
            \\'amount\\': 25.00,
            \\'currency\\': \\'USD\\',
            \\'description\\': \\'Netflix Subscription\\',
            \\'frequency\\': \\'monthly\\',
            \\'start_date\\': (date.today() + timedelta(days=1)).isoformat()
        }
        response = client.post(
            \\'/api/v1/recurring-payments\\',
            headers=headers,
            json=data
        )
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data[\\'message\\'] == \\'Recurring payment created successfully\\'
        assert json_data[\\'recurring_payment\\'][\\'amount\\'] == 25.00

        with app.app_context():
            rp = RecurringPayment.query.filter_by(user_id=\\'test_user_14\\').first()
            assert rp is not None

    def test_execute_recurring_payment_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_15\\'}
        pm = create_test_payment_method(
            \\'test_user_15\\',
            \\'card\\',
            \\'Visa\\',
            {\\'last4\\': \\'6666\\'}
        )
        rp = RecurringPayment(
            user_id=\'test_user_15\',
            payment_method_id=pm.id,
            amount=Decimal(\'10.00\'),
            currency=\'USD\',
            description=\'Spotify\',
            frequency=\'monthly\',
            start_date=date.today() - timedelta(days=30),
            next_execution_date=date.today()
        )
        with app.app_context():
            db.session.add(rp)
            db.session.commit()
            rp_id = rp.id

        response = client.post(
            f\\'/api/v1/recurring-payments/{rp_id}/execute\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'message\\'] == \\'Recurring payment executed successfully\\'
        assert \\'transaction\\' in json_data

        with app.app_context():
            updated_rp = RecurringPayment.query.get(rp_id)
            assert updated_rp.last_execution_date is not None
            assert updated_rp.next_execution_date > date.today()
            transaction = Transaction.query.filter_by(source_id=rp_id).first()
            assert transaction is not None

class TestExchangeRateRoutes:

    def test_get_exchange_rates_empty(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_16\\'}
        response = client.get(
            \\'/api/v1/exchange-rates\\',
            headers=headers
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'exchange_rates\\'] == []
        assert json_data[\\'total\\'] == 0

    def test_create_exchange_rate_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_17\\'}
        data = {
            \\'base_currency\\': \\'USD\\',
            \\'target_currency\\': \\'EUR\\',
            \\'rate\\': 0.92,
            \\'date\\': date.today().isoformat()
        }
        response = client.post(
            \\'/api/v1/exchange-rates\\',
            headers=headers,
            json=data
        )
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data[\\'message\\'] == \\'Exchange rate created successfully\\'
        assert json_data[\\'exchange_rate\\'][\\'rate\\'] == 0.92

        with app.app_context():
            er = ExchangeRate.query.filter_by(base_currency=\\'USD\\', target_currency=\\'EUR\\').first()
            assert er is not None

    def test_get_latest_exchange_rate_success(self, client):
        headers = {\\'X-User-ID\\': \\'test_user_18\\'}
        create_test_exchange_rate(\'USD\', \'GBP\', 0.80, date.today() - timedelta(days=1))
        latest_er = create_test_exchange_rate(\'USD\', \'GBP\', 0.81, date.today())

        response = client.get(
            \\'/api/v1/exchange-rates/latest\\',
            headers=headers,
            query_string={\\'base_currency\\': \\'USD\\', \\'target_currency\\': \\'GBP\\'}
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data[\\'exchange_rate\\'][\\'rate\\'] == 0.81

def create_test_exchange_rate(base, target, rate, date):
    er = ExchangeRate(
        base_currency=base,
        target_currency=target,
        rate=rate,
        date=date
    )
    db.session.add(er)
    db.session.commit()
    return er
