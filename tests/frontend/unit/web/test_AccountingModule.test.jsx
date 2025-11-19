
import { render, screen, fireEvent, waitFor } from \"@testing-library/react\";
import { MemoryRouter } from \"react-router-dom\";
import AccountingModule from \"../../../frontend/web/src/components/AccountingModule\";
import { AppProvider } from \"../../../frontend/web/src/contexts/AppContext\";
import apiClient from \"../../../frontend/web/src/lib/api\";

// Mock apiClient
jest.mock(\"../../../frontend/web/src/lib/api\", () => ({
  getAccounts: jest.fn(() => Promise.resolve({ accounts: [] })),
  getJournalEntries: jest.fn(() => Promise.resolve({ journal_entries: [] })),
  getTrialBalance: jest.fn(() => Promise.resolve({ total_debits: \"0.00\", total_credits: \"0.00\", is_balanced: true })),
  createAccount: jest.fn(() => Promise.resolve({ message: \"Account created\" })),
  createJournalEntry: jest.fn(() => Promise.resolve({ message: \"Entry created\" })),
}));

const renderAccountingModule = () => {
  render(
    <AppProvider>
      <MemoryRouter>
        <AccountingModule />
      </MemoryRouter>
    </AppProvider>
  );
};

describe(\"AccountingModule\", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test(\"renders loading state initially\", () => {
    renderAccountingModule();
    expect(screen.getByText(/Accounting/i)).toBeInTheDocument();
    expect(screen.getByText(/Manage your chart of accounts/i)).toBeInTheDocument();
    expect(screen.getByText(/Overview/i)).toBeInTheDocument();
    expect(screen.getByText(/Accounts/i)).toBeInTheDocument();
    expect(screen.getByText(/Journal Entries/i)).toBeInTheDocument();
    expect(screen.getByText(/Reports/i)).toBeInTheDocument();
  });

  test(\"loads and displays accounts data\", async () => {
    apiClient.getAccounts.mockResolvedValueOnce({
      accounts: [
        { id: \"1\", account_name: \"Cash\", account_code: \"101\", account_type: \"asset\", is_active: true },
        { id: \"2\", account_name: \"Accounts Payable\", account_code: \"201\", account_type: \"liability\", is_active: true },
      ],
    });
    apiClient.getJournalEntries.mockResolvedValueOnce({ journal_entries: [] });
    apiClient.getTrialBalance.mockResolvedValueOnce({ total_debits: \"0.00\", total_credits: \"0.00\", is_balanced: true });

    renderAccountingModule();

    await waitFor(() => {
      expect(screen.getByText(/Cash/i)).toBeInTheDocument();
      expect(screen.getByText(/Accounts Payable/i)).toBeInTheDocument();
      expect(screen.getByText(/asset/i)).toBeInTheDocument();
      expect(screen.getByText(/liability/i)).toBeInTheDocument();
    });
  });

  test(\"loads and displays journal entries data\", async () => {
    apiClient.getAccounts.mockResolvedValueOnce({ accounts: [] });
    apiClient.getJournalEntries.mockResolvedValueOnce({
      journal_entries: [
        { id: \"je1\", entry_number: \"001\", entry_date: \"2024-01-01\", description: \"Initial Entry\", total_amount: \"100.00\", status: \"posted\" },
      ],
    });
    apiClient.getTrialBalance.mockResolvedValueOnce({ total_debits: \"0.00\", total_credits: \"0.00\", is_balanced: true });

    renderAccountingModule();

    await waitFor(() => {
      fireEvent.click(screen.getByRole(\"tab\", { name: /Journal Entries/i }));
      expect(screen.getByText(/Initial Entry/i)).toBeInTheDocument();
      expect(screen.getByText(/\$100.00/i)).toBeInTheDocument();
      expect(screen.getByText(/Posted/i)).toBeInTheDocument();
    });
  });

  test(\"loads and displays trial balance report\", async () => {
    apiClient.getAccounts.mockResolvedValueOnce({ accounts: [] });
    apiClient.getJournalEntries.mockResolvedValueOnce({ journal_entries: [] });
    apiClient.getTrialBalance.mockResolvedValueOnce({
      total_debits: \"1000.00\",
      total_credits: \"1000.00\",
      is_balanced: true,
      as_of_date: \"2024-06-15\",
    });

    renderAccountingModule();

    await waitFor(() => {
      fireEvent.click(screen.getByRole(\"tab\", { name: /Reports/i }));
      expect(screen.getByText(/Trial Balance/i)).toBeInTheDocument();
      expect(screen.getByText(/As of 2024-06-15/i)).toBeInTheDocument();
      expect(screen.getByText(/Total Debits:/i)).toBeInTheDocument();
      expect(screen.getByText(/\$1000.00/i)).toBeInTheDocument();
      expect(screen.getByText(/Balanced/i)).toBeInTheDocument();
    });
  });

  test(\"allows adding a new account\", async () => {
    apiClient.getAccounts.mockResolvedValueOnce({ accounts: [] });
    apiClient.getJournalEntries.mockResolvedValueOnce({ journal_entries: [] });
    apiClient.getTrialBalance.mockResolvedValueOnce({ total_debits: \"0.00\", total_credits: \"0.00\", is_balanced: true });
    apiClient.createAccount.mockResolvedValueOnce({ message: \"Account created\" });

    renderAccountingModule();

    await waitFor(() => {
      fireEvent.click(screen.getByRole(\"tab\", { name: /Accounts/i }));
    });

    fireEvent.click(screen.getByRole(\"button\", { name: /Add Account/i }));

    await waitFor(() => {
      expect(screen.getByText(/Create New Account/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/Account Name/i), { target: { value: \"New Test Account\" } });
    fireEvent.change(screen.getByLabelText(/Account Code/i), { target: { value: \"999\" } });
    fireEvent.change(screen.getByLabelText(/Account Type/i), { target: { value: \"revenue\" } });
    fireEvent.change(screen.getByLabelText(/Description/i), { target: { value: \"A new account for testing\" } });

    fireEvent.click(screen.getByRole(\"button\", { name: /Create Account/i }));

    await waitFor(() => {
      expect(apiClient.createAccount).toHaveBeenCalledWith({
        account_name: \"New Test Account\",
        account_code: \"999\",
        account_type: \"revenue\",
        description: \"A new account for testing\",
      });
      expect(screen.queryByText(/Create New Account/i)).not.toBeInTheDocument(); // Dialog closes
    });
  });

  test(\"allows creating a new journal entry\", async () => {
    apiClient.getAccounts.mockResolvedValueOnce({
      accounts: [
        { id: \"1\", account_name: \"Cash\", account_code: \"101\", account_type: \"asset\", is_active: true },
        { id: \"2\", account_name: \"Revenue\", account_code: \"401\", account_type: \"revenue\", is_active: true },
      ],
    });
    apiClient.getJournalEntries.mockResolvedValueOnce({ journal_entries: [] });
    apiClient.getTrialBalance.mockResolvedValueOnce({ total_debits: \"0.00\", total_credits: \"0.00\", is_balanced: true });
    apiClient.createJournalEntry.mockResolvedValueOnce({ message: \"Entry created\" });

    renderAccountingModule();

    await waitFor(() => {
      fireEvent.click(screen.getByRole(\"tab\", { name: /Journal Entries/i }));
    });

    fireEvent.click(screen.getByRole(\"button\", { name: /New Entry/i }));

    await waitFor(() => {
      expect(screen.getByText(/Create Journal Entry/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/Entry Date/i), { target: { value: \"2024-06-15\" } });
    fireEvent.change(screen.getByLabelText(/Description/i), { target: { value: \"Test Journal Entry\" } });

    // Add first line item (Debit)
    fireEvent.click(screen.getByRole(\"button\", { name: /Add Line Item/i }));
    fireEvent.change(screen.getByLabelText(/Account:/i), { target: { value: \"1\" } }); // Cash
    fireEvent.change(screen.getByLabelText(/Debit:/i), { target: { value: \"500\" } });

    // Add second line item (Credit)
    fireEvent.click(screen.getByRole(\"button\", { name: /Add Line Item/i }));
    fireEvent.change(screen.getAllByLabelText(/Account:/i)[1], { target: { value: \"2\" } }); // Revenue
    fireEvent.change(screen.getByLabelText(/Credit:/i), { target: { value: \"500\" } });

    fireEvent.click(screen.getByRole(\"button\", { name: /Save Journal Entry/i }));

    await waitFor(() => {
      expect(apiClient.createJournalEntry).toHaveBeenCalledWith({
        entry_date: \"2024-06-15\",
        description: \"Test Journal Entry\",
        line_items: [
          { account_id: \"1\", debit: 500, credit: 0 },
          { account_id: \"2\", debit: 0, credit: 500 },
        ],
      });
      expect(screen.queryByText(/Create Journal Entry/i)).not.toBeInTheDocument(); // Dialog closes
    });
  });
});
