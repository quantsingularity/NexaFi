
import { test, expect } from '@playwright/test';

test.describe('Web Application E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Log in before each test to ensure authenticated state
    await page.goto('http://localhost:3000/auth');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button:has-text("Sign In")');
    await page.waitForURL('http://localhost:3000/dashboard');
  });

  test('User can navigate to Payments module', async ({ page }) => {
    await page.goto('http://localhost:3000/payments');
    await expect(page.locator('h1')).toContainText('Payments');
    await expect(page.getByText('Manage your transactions, wallets, and payment methods')).toBeVisible();
  });

  test('User can navigate to AI Insights module', async ({ page }) => {
    await page.goto('http://localhost:3000/ai-insights');
    await expect(page.locator('h1')).toContainText('AI Insights');
    await expect(page.getByText('Leverage AI for cash flow predictions and financial insights')).toBeVisible();
  });

  test('User can navigate to Settings module', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');
    await expect(page.locator('h1')).toContainText('Settings');
    await expect(page.getByText('Manage your profile and application settings')).toBeVisible();
  });

  test('User can log out', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    // Assuming there's a logout button or link in the Layout component
    await page.click('button:has-text("Logout")');
    await page.waitForURL('http://localhost:3000/');
    await expect(page.locator('h1')).toContainText('Welcome to NexaFi');
  });

  test('User can create a new account (from homepage)', async ({ page }) => {
    await page.goto('http://localhost:3000/');
    await page.click('button:has-text("Get Started")');
    await page.waitForURL('http://localhost:3000/auth');

    // Switch to Sign Up tab
    await page.click('button:has-text("Sign Up")');

    // Fill in registration form
    await page.fill('input[name="first_name"]', 'NewE2E');
    await page.fill('input[name="last_name"]', 'User');
    await page.fill('input[name="email"]', `new.e2e.user+${Date.now()}@example.com`); // Unique email
    await page.fill('input[name="password"]', 'newPassword123');
    await page.fill('input[name="confirmPassword"]', 'newPassword123');
    await page.fill('input[name="business_name"]', 'New E2E Business');

    await page.click('button:has-text("Create Account")');

    // Expect to be redirected to dashboard after registration
    await page.waitForURL('http://localhost:3000/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('User can view accounting module and add an account', async ({ page }) => {
    await page.goto('http://localhost:3000/accounting');
    await expect(page.locator('h1')).toContainText('Accounting');
    await expect(page.getByText('Chart of Accounts')).toBeVisible();

    // Click 'Add Account' button
    await page.click('button:has-text("Add Account")');

    // Fill in new account form
    await page.fill('input[id="account_name"]', 'E2E Test Account');
    await page.fill('input[id="account_code"]', '9999');
    await page.click('div[role="combobox"]:has-text("Select account type")');
    await page.click('div[role="option"]:has-text("Revenue")');
    await page.fill('textarea[id="description"]', 'Account created via E2E test');

    await page.click('button:has-text("Create Account")');

    // Verify account is added (might require scrolling or searching)
    await expect(page.getByText('E2E Test Account')).toBeVisible();
  });

  test('User can view payments module and create a transaction', async ({ page }) => {
    await page.goto('http://localhost:3000/payments');
    await expect(page.locator('h1')).toContainText('Payments');

    // Click 'New Transaction' button
    await page.click('button:has-text("New Transaction")');

    // Fill in transaction form
    await page.fill('input[id="amount"]', '150.75');
    await page.fill('input[id="description"]', 'E2E Test Transaction');
    await page.click('div[role="combobox"]:has-text("Select transaction type")');
    await page.click('div[role="option"]:has-text("Expense")');
    await page.click('div[role="combobox"]:has-text("Select payment method")');
    // Assuming there's at least one payment method available, select the first one
    await page.locator('div[role="option"]').first().click();

    await page.click('button:has-text("Create Transaction")');

    // Verify transaction is created
    await expect(page.getByText('E2E Test Transaction')).toBeVisible();
  });
});
