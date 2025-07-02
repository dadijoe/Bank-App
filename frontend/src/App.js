import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [currentView, setCurrentView] = useState('dashboard');
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Auth forms state
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    address: '',
    date_of_birth: ''
  });

  // Transfer form state
  const [transferData, setTransferData] = useState({
    from_account_id: '',
    to_account_id: '',
    to_email: '',
    amount: '',
    transfer_type: 'internal',
    description: '',
    recipient_name: '',
    recipient_bank: '',
    routing_number: ''
  });

  // Admin forms state
  const [adminData, setAdminData] = useState({
    account_id: '',
    amount: '',
    transaction_type: 'credit',
    description: '',
    backdate: ''
  });

  const [allUsers, setAllUsers] = useState([]);
  const [allAccounts, setAllAccounts] = useState([]);
  const [allTransactions, setAllTransactions] = useState([]);

  useEffect(() => {
    if (token) {
      fetchUserData();
    }
  }, [token]);

  const apiCall = async (endpoint, options = {}) => {
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` })
      },
      ...options
    };

    const response = await fetch(`${BACKEND_URL}/api${endpoint}`, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'API request failed');
    }

    return data;
  };

  const fetchUserData = async () => {
    try {
      setLoading(true);
      const accountsData = await apiCall('/accounts');
      setAccounts(accountsData.accounts);
      
      // Get user info from token
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser(payload);
      
      setError('');
    } catch (err) {
      setError(err.message);
      if (err.message.includes('Token')) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const data = await apiCall(endpoint, {
        method: 'POST',
        body: JSON.stringify(formData)
      });

      localStorage.setItem('token', data.token);
      setToken(data.token);
      setUser(data.user);
      
      if (!isLogin) {
        setAccounts(data.accounts);
      }
      
      setCurrentView('dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setAccounts([]);
    setTransactions([]);
    setCurrentView('dashboard');
    setFormData({
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      phone: '',
      address: '',
      date_of_birth: ''
    });
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      await apiCall('/transfers', {
        method: 'POST',
        body: JSON.stringify({
          ...transferData,
          amount: parseFloat(transferData.amount)
        })
      });

      alert('Transfer completed successfully!');
      fetchUserData(); // Refresh account data
      setTransferData({
        from_account_id: '',
        to_account_id: '',
        to_email: '',
        amount: '',
        transfer_type: 'internal',
        description: '',
        recipient_name: '',
        recipient_bank: '',
        routing_number: ''
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async (accountId) => {
    try {
      setLoading(true);
      const data = await apiCall(`/accounts/${accountId}/transactions`);
      setTransactions(data.transactions);
      setCurrentView('transactions');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAdminData = async () => {
    if (user?.role !== 'admin' && user?.role !== 'super_admin') return;
    
    try {
      setLoading(true);
      const [usersData, accountsData, transactionsData] = await Promise.all([
        apiCall('/admin/users'),
        apiCall('/admin/accounts'),
        apiCall('/admin/transactions')
      ]);
      
      setAllUsers(usersData.users);
      setAllAccounts(accountsData.accounts);
      setAllTransactions(transactionsData.transactions);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAdminCreditDebit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      await apiCall('/admin/credit-debit', {
        method: 'POST',
        body: JSON.stringify({
          ...adminData,
          amount: parseFloat(adminData.amount)
        })
      });

      alert(`Account ${adminData.transaction_type} completed successfully!`);
      fetchAdminData(); // Refresh admin data
      setAdminData({
        account_id: '',
        amount: '',
        transaction_type: 'credit',
        description: '',
        backdate: ''
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Auth form component
  const AuthForm = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Demo Bank</h1>
          <p className="text-gray-600">Secure Online Banking</p>
        </div>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <form onSubmit={handleAuth} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {!isLogin && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                  <input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition duration-200"
          >
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>

        {isLogin && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Demo Credentials:</p>
            <p className="text-xs text-gray-500">Admin: admin@demobank.com / admin123</p>
            <p className="text-xs text-gray-500">Or create a new customer account</p>
          </div>
        )}
      </div>
    </div>
  );

  // Navigation component
  const Navigation = () => (
    <nav className="bg-blue-900 text-white p-4 shadow-lg">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold">Demo Bank</h1>
          <span className="text-blue-200">|</span>
          <span className="text-blue-200">Welcome, {user?.first_name || user?.email}</span>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setCurrentView('dashboard')}
            className={`px-4 py-2 rounded-lg transition ${currentView === 'dashboard' ? 'bg-blue-700' : 'hover:bg-blue-800'}`}
          >
            Dashboard
          </button>
          
          <button
            onClick={() => setCurrentView('transfer')}
            className={`px-4 py-2 rounded-lg transition ${currentView === 'transfer' ? 'bg-blue-700' : 'hover:bg-blue-800'}`}
          >
            Transfer
          </button>
          
          {(user?.role === 'admin' || user?.role === 'super_admin') && (
            <button
              onClick={() => {
                setCurrentView('admin');
                fetchAdminData();
              }}
              className={`px-4 py-2 rounded-lg transition ${currentView === 'admin' ? 'bg-blue-700' : 'hover:bg-blue-800'}`}
            >
              Admin Panel
            </button>
          )}
          
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 rounded-lg hover:bg-red-700 transition"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );

  // Dashboard component
  const Dashboard = () => (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">Account Overview</h2>
        <p className="text-gray-600">Manage your accounts and view recent activity</p>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts.map((account) => (
          <div key={account.account_id} className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 capitalize">
                  {account.account_type} Account
                </h3>
                <p className="text-sm text-gray-500">****{account.account_number.slice(-4)}</p>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                account.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {account.status}
              </span>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-500 mb-1">Available Balance</p>
              <p className="text-2xl font-bold text-gray-800">{formatCurrency(account.balance)}</p>
            </div>
            
            <button
              onClick={() => fetchTransactions(account.account_id)}
              className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              View Transactions
            </button>
          </div>
        ))}
      </div>

      <div className="mt-8 grid md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-2">Quick Transfer</h3>
          <p className="text-sm opacity-90 mb-4">Transfer money between accounts instantly</p>
          <button
            onClick={() => setCurrentView('transfer')}
            className="bg-white text-green-600 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition"
          >
            Start Transfer
          </button>
        </div>
        
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-2">Wire Transfer</h3>
          <p className="text-sm opacity-90 mb-4">Send money internationally with wire transfers</p>
          <button
            onClick={() => {
              setCurrentView('transfer');
              setTransferData({...transferData, transfer_type: 'wire'});
            }}
            className="bg-white text-purple-600 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition"
          >
            Send Wire
          </button>
        </div>
        
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-2">Account Statements</h3>
          <p className="text-sm opacity-90 mb-4">Download your monthly account statements</p>
          <button className="bg-white text-orange-600 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition">
            Download
          </button>
        </div>
      </div>
    </div>
  );

  // Transfer component
  const Transfer = () => (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">Transfer Money</h2>
        <p className="text-gray-600">Send money securely and quickly</p>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
        <form onSubmit={handleTransfer} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">From Account</label>
              <select
                value={transferData.from_account_id}
                onChange={(e) => setTransferData({...transferData, from_account_id: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select source account</option>
                {accounts.map((account) => (
                  <option key={account.account_id} value={account.account_id}>
                    {account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)} - {formatCurrency(account.balance)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Transfer Type</label>
              <select
                value={transferData.transfer_type}
                onChange={(e) => setTransferData({...transferData, transfer_type: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="internal">Internal Transfer</option>
                <option value="domestic">Domestic Transfer (ACH)</option>
                <option value="wire">Wire Transfer</option>
              </select>
            </div>
          </div>

          {transferData.transfer_type === 'internal' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">To Account</label>
              <select
                value={transferData.to_account_id}
                onChange={(e) => setTransferData({...transferData, to_account_id: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select destination account</option>
                {accounts.filter(acc => acc.account_id !== transferData.from_account_id).map((account) => (
                  <option key={account.account_id} value={account.account_id}>
                    {account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)} - {formatCurrency(account.balance)}
                  </option>
                ))}
              </select>
            </div>
          )}

          {(transferData.transfer_type === 'domestic' || transferData.transfer_type === 'wire') && (
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Recipient Name</label>
                <input
                  type="text"
                  value={transferData.recipient_name}
                  onChange={(e) => setTransferData({...transferData, recipient_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Recipient Bank</label>
                <input
                  type="text"
                  value={transferData.recipient_bank}
                  onChange={(e) => setTransferData({...transferData, recipient_bank: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Routing Number</label>
                <input
                  type="text"
                  value={transferData.routing_number}
                  onChange={(e) => setTransferData({...transferData, routing_number: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Amount</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={transferData.amount}
                onChange={(e) => setTransferData({...transferData, amount: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <input
                type="text"
                value={transferData.description}
                onChange={(e) => setTransferData({...transferData, description: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Payment description"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition duration-200"
          >
            {loading ? 'Processing Transfer...' : 'Send Transfer'}
          </button>
        </form>
      </div>
    </div>
  );

  // Transactions component
  const Transactions = () => (
    <div className="container mx-auto p-6">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Transaction History</h2>
          <p className="text-gray-600">View your recent account activity</p>
        </div>
        
        <button
          onClick={() => setCurrentView('dashboard')}
          className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition"
        >
          Back to Dashboard
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactions.map((transaction) => (
                <tr key={transaction.transaction_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(transaction.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {transaction.description || 'Transfer'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                    {transaction.transfer_type?.replace('_', ' ')}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                    transaction.to_account_id ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {transaction.to_account_id ? '+' : '-'}{formatCurrency(transaction.amount)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      transaction.status === 'completed' ? 'bg-green-100 text-green-800' :
                      transaction.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {transaction.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {transactions.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500">No transactions found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Admin Panel component
  const AdminPanel = () => (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">Admin Panel</h2>
        <p className="text-gray-600">Manage users, accounts, and transactions</p>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Credit/Debit Form */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Credit/Debit Account</h3>
        
        <form onSubmit={handleAdminCreditDebit} className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Account</label>
            <select
              value={adminData.account_id}
              onChange={(e) => setAdminData({...adminData, account_id: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="">Select account</option>
              {allAccounts.map((account) => (
                <option key={account.account_id} value={account.account_id}>
                  {account.user_name} - {account.account_type} ({formatCurrency(account.balance)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Transaction Type</label>
            <select
              value={adminData.transaction_type}
              onChange={(e) => setAdminData({...adminData, transaction_type: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="credit">Credit (Add Money)</option>
              <option value="debit">Debit (Remove Money)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Amount</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={adminData.amount}
              onChange={(e) => setAdminData({...adminData, amount: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <input
              type="text"
              value={adminData.description}
              onChange={(e) => setAdminData({...adminData, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {user?.role === 'super_admin' && (
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Backdate (Optional)</label>
              <input
                type="datetime-local"
                value={adminData.backdate}
                onChange={(e) => setAdminData({...adminData, backdate: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          )}

          <div className="md:col-span-2">
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {loading ? 'Processing...' : `${adminData.transaction_type === 'credit' ? 'Credit' : 'Debit'} Account`}
            </button>
          </div>
        </form>
      </div>

      {/* Admin Tables */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* Users Table */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Users</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">Name</th>
                  <th className="px-4 py-2 text-left">Email</th>
                  <th className="px-4 py-2 text-left">Role</th>
                  <th className="px-4 py-2 text-left">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {allUsers.slice(0, 10).map((user) => (
                  <tr key={user.user_id}>
                    <td className="px-4 py-2">{user.first_name} {user.last_name}</td>
                    <td className="px-4 py-2">{user.email}</td>
                    <td className="px-4 py-2 capitalize">{user.role}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        user.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {user.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Accounts Table */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Accounts</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">User</th>
                  <th className="px-4 py-2 text-left">Type</th>
                  <th className="px-4 py-2 text-left">Balance</th>
                  <th className="px-4 py-2 text-left">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {allAccounts.slice(0, 10).map((account) => (
                  <tr key={account.account_id}>
                    <td className="px-4 py-2">{account.user_name}</td>
                    <td className="px-4 py-2 capitalize">{account.account_type}</td>
                    <td className="px-4 py-2 font-medium">{formatCurrency(account.balance)}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        account.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {account.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Transactions</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left">Date</th>
                <th className="px-4 py-2 text-left">Type</th>
                <th className="px-4 py-2 text-left">Amount</th>
                <th className="px-4 py-2 text-left">Description</th>
                <th className="px-4 py-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {allTransactions.slice(0, 15).map((transaction) => (
                <tr key={transaction.transaction_id}>
                  <td className="px-4 py-2">{formatDate(transaction.created_at)}</td>
                  <td className="px-4 py-2 capitalize">{transaction.transfer_type?.replace('_', ' ')}</td>
                  <td className="px-4 py-2 font-medium">{formatCurrency(transaction.amount)}</td>
                  <td className="px-4 py-2">{transaction.description}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      transaction.status === 'completed' ? 'bg-green-100 text-green-800' :
                      transaction.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {transaction.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  // Main render
  if (!token) {
    return <AuthForm />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      {loading && (
        <div className="fixed top-0 left-0 w-full h-1 bg-blue-600 animate-pulse z-50"></div>
      )}
      
      {currentView === 'dashboard' && <Dashboard />}
      {currentView === 'transfer' && <Transfer />}
      {currentView === 'transactions' && <Transactions />}
      {currentView === 'admin' && (user?.role === 'admin' || user?.role === 'super_admin') && <AdminPanel />}
    </div>
  );
}

export default App;