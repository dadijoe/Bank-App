import requests
import unittest
import json
import uuid
from datetime import datetime

class BankingAPITest(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://9598cf7d-eac3-44e0-8714-dfe8176f5812.preview.emergentagent.com/api"
        self.customer_token = None
        self.admin_token = None
        self.customer_user_id = None
        self.customer_accounts = []
        
        # Generate unique email for testing
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.test_email = f"test_user_{timestamp}@example.com"
        
        # Admin credentials
        self.admin_email = "admin@demobank.com"
        self.admin_password = "admin123"

    def test_01_health_check(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        print("✅ Health check endpoint is working")

    def test_02_register_customer(self):
        """Test customer registration"""
        registration_data = {
            "email": self.test_email,
            "password": "Test123!",
            "first_name": "Test",
            "last_name": "User",
            "phone": "555-1234",
            "address": "123 Test St",
            "date_of_birth": "1990-01-01"
        }
        
        response = requests.post(f"{self.base_url}/auth/register", json=registration_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("token", data)
        self.assertIn("user", data)
        self.assertIn("accounts", data)
        
        # Save token and user data for subsequent tests
        self.customer_token = data["token"]
        self.customer_user_id = data["user"]["user_id"]
        self.customer_accounts = data["accounts"]
        
        # Verify accounts were created
        self.assertEqual(len(self.customer_accounts), 2)
        self.assertEqual(self.customer_accounts[0]["account_type"], "checking")
        self.assertEqual(self.customer_accounts[1]["account_type"], "savings")
        
        print(f"✅ Customer registration successful: {self.test_email}")

    def test_03_login_admin(self):
        """Test admin login"""
        login_data = {
            "email": self.admin_email,
            "password": self.admin_password
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["role"], "super_admin")
        
        # Save admin token for subsequent tests
        self.admin_token = data["token"]
        print(f"✅ Admin login successful: {self.admin_email}")

    def test_04_get_customer_accounts(self):
        """Test retrieving customer accounts"""
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.get(f"{self.base_url}/accounts", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("accounts", data)
        self.assertEqual(len(data["accounts"]), 2)
        
        # Verify account balances
        checking_account = next((acc for acc in data["accounts"] if acc["account_type"] == "checking"), None)
        savings_account = next((acc for acc in data["accounts"] if acc["account_type"] == "savings"), None)
        
        self.assertIsNotNone(checking_account)
        self.assertIsNotNone(savings_account)
        self.assertEqual(checking_account["balance"], 1000.0)
        self.assertEqual(savings_account["balance"], 5000.0)
        
        print("✅ Customer accounts retrieved successfully")

    def test_05_internal_transfer(self):
        """Test internal transfer between accounts"""
        if not self.customer_accounts or len(self.customer_accounts) < 2:
            self.skipTest("Not enough accounts to test transfer")
        
        from_account = self.customer_accounts[0]
        to_account = self.customer_accounts[1]
        
        transfer_data = {
            "from_account_id": from_account["account_id"],
            "to_account_id": to_account["account_id"],
            "amount": 100.0,
            "transfer_type": "internal",
            "description": "Test internal transfer"
        }
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.post(f"{self.base_url}/transfers", json=transfer_data, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("transaction", data)
        self.assertEqual(data["transaction"]["status"], "completed")
        
        # Verify account balances after transfer
        response = requests.get(f"{self.base_url}/accounts", headers=headers)
        accounts_data = response.json()
        
        updated_from_account = next((acc for acc in accounts_data["accounts"] 
                                    if acc["account_id"] == from_account["account_id"]), None)
        updated_to_account = next((acc for acc in accounts_data["accounts"] 
                                  if acc["account_id"] == to_account["account_id"]), None)
        
        self.assertEqual(updated_from_account["balance"], from_account["balance"] - 100.0)
        self.assertEqual(updated_to_account["balance"], to_account["balance"] + 100.0)
        
        print("✅ Internal transfer completed successfully")

    def test_06_external_transfer(self):
        """Test external transfer (wire)"""
        if not self.customer_accounts:
            self.skipTest("No accounts to test transfer")
        
        from_account = self.customer_accounts[0]
        
        transfer_data = {
            "from_account_id": from_account["account_id"],
            "amount": 50.0,
            "transfer_type": "wire",
            "description": "Test wire transfer",
            "recipient_name": "External User",
            "recipient_bank": "External Bank",
            "routing_number": "123456789"
        }
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.post(f"{self.base_url}/transfers", json=transfer_data, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("transaction", data)
        self.assertEqual(data["transaction"]["status"], "pending")
        
        # Verify account balance after transfer
        response = requests.get(f"{self.base_url}/accounts", headers=headers)
        accounts_data = response.json()
        
        updated_from_account = next((acc for acc in accounts_data["accounts"] 
                                    if acc["account_id"] == from_account["account_id"]), None)
        
        self.assertEqual(updated_from_account["balance"], from_account["balance"] - 150.0)  # 100 from previous test + 50 from this test
        
        print("✅ Wire transfer completed successfully")

    def test_07_get_transaction_history(self):
        """Test retrieving transaction history"""
        if not self.customer_accounts:
            self.skipTest("No accounts to test transaction history")
        
        account_id = self.customer_accounts[0]["account_id"]
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        
        response = requests.get(f"{self.base_url}/accounts/{account_id}/transactions", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("transactions", data)
        self.assertGreaterEqual(len(data["transactions"]), 2)  # Should have at least 2 transactions from previous tests
        
        print("✅ Transaction history retrieved successfully")

    def test_08_admin_get_all_users(self):
        """Test admin retrieving all users"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{self.base_url}/admin/users", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("users", data)
        self.assertGreaterEqual(len(data["users"]), 2)  # Should have at least admin and test user
        
        # Verify our test user is in the list
        test_user = next((user for user in data["users"] if user["email"] == self.test_email), None)
        self.assertIsNotNone(test_user)
        
        print("✅ Admin retrieved all users successfully")

    def test_09_admin_get_all_accounts(self):
        """Test admin retrieving all accounts"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{self.base_url}/admin/accounts", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("accounts", data)
        self.assertGreaterEqual(len(data["accounts"]), 2)  # Should have at least 2 accounts for test user
        
        print("✅ Admin retrieved all accounts successfully")

    def test_10_admin_credit_account(self):
        """Test admin crediting an account"""
        if not self.admin_token or not self.customer_accounts:
            self.skipTest("Admin token or customer accounts not available")
        
        account_id = self.customer_accounts[0]["account_id"]
        
        credit_data = {
            "account_id": account_id,
            "amount": 200.0,
            "transaction_type": "credit",
            "description": "Admin test credit"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.post(f"{self.base_url}/admin/credit-debit", json=credit_data, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("transaction", data)
        self.assertEqual(data["transaction"]["status"], "completed")
        
        # Verify account balance after credit
        customer_headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.get(f"{self.base_url}/accounts", headers=customer_headers)
        accounts_data = response.json()
        
        updated_account = next((acc for acc in accounts_data["accounts"] 
                               if acc["account_id"] == account_id), None)
        
        # Balance should be original - 150 (from transfers) + 200 (from credit) = original + 50
        self.assertEqual(updated_account["balance"], self.customer_accounts[0]["balance"] - 150.0 + 200.0)
        
        print("✅ Admin credited account successfully")

    def test_11_admin_get_all_transactions(self):
        """Test admin retrieving all transactions"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{self.base_url}/admin/transactions", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("transactions", data)
        self.assertGreaterEqual(len(data["transactions"]), 3)  # Should have at least 3 transactions from previous tests
        
        print("✅ Admin retrieved all transactions successfully")

    def test_12_super_admin_backdate_transaction(self):
        """Test super admin backdating a transaction"""
        if not self.admin_token or not self.customer_accounts:
            self.skipTest("Admin token or customer accounts not available")
        
        account_id = self.customer_accounts[1]["account_id"]
        backdate = "2025-01-01T12:00:00"
        
        credit_data = {
            "account_id": account_id,
            "amount": 100.0,
            "transaction_type": "credit",
            "description": "Backdated credit",
            "backdate": backdate
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.post(f"{self.base_url}/admin/credit-debit", json=credit_data, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("transaction", data)
        self.assertEqual(data["transaction"]["status"], "completed")
        self.assertTrue(data["transaction"]["backdated"])
        
        print("✅ Super admin backdated transaction successfully")

if __name__ == "__main__":
    # Run tests in order
    unittest.main(argv=['first-arg-is-ignored'], exit=False)