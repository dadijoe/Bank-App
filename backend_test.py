import requests
import json
import uuid
from datetime import datetime, timedelta

class BankingAPITester:
    def __init__(self):
        self.base_url = "https://9598cf7d-eac3-44e0-8714-dfe8176f5812.preview.emergentagent.com/api"
        self.customer_token = None
        self.admin_token = None
        self.customer_user_id = None
        self.customer_accounts = []
        self.transaction_id = None
        
        # Generate unique email for testing
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.test_email = f"test_user_{timestamp}@example.com"
        
        # Admin credentials
        self.admin_email = "admin@demobank.com"
        self.admin_password = "admin123"
        
        # Failed login tracking
        self.failed_login_attempts = 0
        
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, func):
        """Run a test function and track results"""
        self.tests_run += 1
        print(f"\n🔍 Testing: {name}")
        
        try:
            result = func()
            if result:
                self.tests_passed += 1
                print(f"✅ PASSED: {name}")
            else:
                print(f"❌ FAILED: {name}")
            return result
        except Exception as e:
            print(f"❌ ERROR: {name} - {str(e)}")
            return False

    def test_health_check(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.base_url}/health")
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            return False
            
        data = response.json()
        if data.get("status") != "healthy":
            print(f"  Expected 'healthy' status, got {data.get('status')}")
            return False
            
        print("  Health check endpoint is working")
        return True

    def test_register_customer(self):
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
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        data = response.json()
        if "token" not in data or "user" not in data or "accounts" not in data:
            print("  Missing expected data in response")
            return False
        
        # Save token and user data for subsequent tests
        self.customer_token = data["token"]
        self.customer_user_id = data["user"]["user_id"]
        self.customer_accounts = data["accounts"]
        
        # Verify accounts were created
        if len(self.customer_accounts) != 2:
            print(f"  Expected 2 accounts, got {len(self.customer_accounts)}")
            return False
            
        if self.customer_accounts[0]["account_type"] != "checking" or self.customer_accounts[1]["account_type"] != "savings":
            print("  Expected checking and savings accounts")
            return False
        
        print(f"  Customer registration successful: {self.test_email}")
        print(f"  Created accounts: {len(self.customer_accounts)}")
        return True

    def test_login_admin(self):
        """Test admin login"""
        login_data = {
            "email": self.admin_email,
            "password": self.admin_password
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        data = response.json()
        if "token" not in data or "user" not in data:
            print("  Missing expected data in response")
            return False
            
        if data["user"]["role"] != "super_admin":
            print(f"  Expected role 'super_admin', got {data['user']['role']}")
            return False
        
        # Save admin token for subsequent tests
        self.admin_token = data["token"]
        print(f"  Admin login successful: {self.admin_email}")
        return True

    def test_get_customer_accounts(self):
        """Test retrieving customer accounts"""
        if not self.customer_token:
            print("  Customer token not available")
            return False
            
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.get(f"{self.base_url}/accounts", headers=headers)
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        if "accounts" not in data:
            print("  Missing accounts in response")
            return False
            
        if len(data["accounts"]) != 2:
            print(f"  Expected 2 accounts, got {len(data['accounts'])}")
            return False
        
        # Verify account balances
        checking_account = next((acc for acc in data["accounts"] if acc["account_type"] == "checking"), None)
        savings_account = next((acc for acc in data["accounts"] if acc["account_type"] == "savings"), None)
        
        if not checking_account or not savings_account:
            print("  Missing checking or savings account")
            return False
            
        if checking_account["balance"] != 1000.0:
            print(f"  Expected checking balance 1000.0, got {checking_account['balance']}")
            return False
            
        if savings_account["balance"] != 5000.0:
            print(f"  Expected savings balance 5000.0, got {savings_account['balance']}")
            return False
        
        print("  Customer accounts retrieved successfully")
        print(f"  Checking balance: {checking_account['balance']}")
        print(f"  Savings balance: {savings_account['balance']}")
        return True

    def test_internal_transfer(self):
        """Test internal transfer between accounts"""
        if not self.customer_token or not self.customer_accounts or len(self.customer_accounts) < 2:
            print("  Not enough accounts to test transfer")
            return False
        
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
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        if "transaction" not in data:
            print("  Missing transaction in response")
            return False
            
        if data["transaction"]["status"] != "completed":
            print(f"  Expected status 'completed', got {data['transaction']['status']}")
            return False
        
        # Verify account balances after transfer
        response = requests.get(f"{self.base_url}/accounts", headers=headers)
        if response.status_code != 200:
            print(f"  Failed to get updated accounts: {response.status_code}")
            return False
            
        accounts_data = response.json()
        
        updated_from_account = next((acc for acc in accounts_data["accounts"] 
                                    if acc["account_id"] == from_account["account_id"]), None)
        updated_to_account = next((acc for acc in accounts_data["accounts"] 
                                  if acc["account_id"] == to_account["account_id"]), None)
        
        if not updated_from_account or not updated_to_account:
            print("  Failed to find updated accounts")
            return False
            
        expected_from_balance = from_account["balance"] - 100.0
        expected_to_balance = to_account["balance"] + 100.0
        
        if updated_from_account["balance"] != expected_from_balance:
            print(f"  Expected from_account balance {expected_from_balance}, got {updated_from_account['balance']}")
            return False
            
        if updated_to_account["balance"] != expected_to_balance:
            print(f"  Expected to_account balance {expected_to_balance}, got {updated_to_account['balance']}")
            return False
        
        print("  Internal transfer completed successfully")
        print(f"  From account new balance: {updated_from_account['balance']}")
        print(f"  To account new balance: {updated_to_account['balance']}")
        return True

    def test_admin_credit_account(self):
        """Test admin crediting an account"""
        if not self.admin_token or not self.customer_accounts:
            print("  Admin token or customer accounts not available")
            return False
        
        account_id = self.customer_accounts[0]["account_id"]
        
        credit_data = {
            "account_id": account_id,
            "amount": 200.0,
            "transaction_type": "credit",
            "description": "Admin test credit"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.post(f"{self.base_url}/admin/credit-debit", json=credit_data, headers=headers)
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        if "transaction" not in data:
            print("  Missing transaction in response")
            return False
            
        if data["transaction"]["status"] != "completed":
            print(f"  Expected status 'completed', got {data['transaction']['status']}")
            return False
        
        # Verify account balance after credit
        customer_headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.get(f"{self.base_url}/accounts", headers=customer_headers)
        
        if response.status_code != 200:
            print(f"  Failed to get updated accounts: {response.status_code}")
            return False
            
        accounts_data = response.json()
        
        updated_account = next((acc for acc in accounts_data["accounts"] 
                               if acc["account_id"] == account_id), None)
        
        if not updated_account:
            print("  Failed to find updated account")
            return False
            
        # Balance should be original - 100 (from transfer) + 200 (from credit) = original + 100
        expected_balance = self.customer_accounts[0]["balance"] - 100.0 + 200.0
        
        if updated_account["balance"] != expected_balance:
            print(f"  Expected balance {expected_balance}, got {updated_account['balance']}")
            return False
        
        print("  Admin credited account successfully")
        print(f"  New balance: {updated_account['balance']}")
        return True

    def test_transaction_filtering(self):
        """Test transaction filtering by date and type"""
        if not self.customer_token or not self.customer_accounts:
            print("  Customer token or accounts not available")
            return False
        
        account_id = self.customer_accounts[0]["account_id"]
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        
        # Get transactions with filters
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Test date filtering
        params = {
            "start_date": yesterday,
            "end_date": today,
            "limit": 25
        }
        
        response = requests.get(
            f"{self.base_url}/accounts/{account_id}/transactions", 
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        if "transactions" not in data:
            print("  Missing transactions in response")
            return False
        
        # Test transaction type filtering
        params = {
            "transaction_type": "internal",
            "limit": 25
        }
        
        response = requests.get(
            f"{self.base_url}/accounts/{account_id}/transactions", 
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        if "transactions" not in data:
            print("  Missing transactions in response")
            return False
        
        # Verify all returned transactions are of type "internal"
        for transaction in data["transactions"]:
            if transaction["transfer_type"] != "internal":
                print(f"  Expected transaction type 'internal', got {transaction['transfer_type']}")
                return False
        
        print("  Transaction filtering works correctly")
        return True
        
    def test_account_statement(self):
        """Test account statement generation"""
        if not self.customer_token or not self.customer_accounts:
            print("  Customer token or accounts not available")
            return False
        
        account_id = self.customer_accounts[0]["account_id"]
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        
        # Get current month statement
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        params = {
            "month": current_month,
            "year": current_year
        }
        
        response = requests.get(
            f"{self.base_url}/accounts/{account_id}/statement", 
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        if "statement" not in data:
            print("  Missing statement in response")
            return False
        
        statement = data["statement"]
        
        # Verify statement contains required fields
        required_fields = [
            "account_id", "account_number", "account_type", "statement_period",
            "opening_balance", "total_credits", "total_debits", "closing_balance",
            "transaction_count", "transactions"
        ]
        
        for field in required_fields:
            if field not in statement:
                print(f"  Missing required field in statement: {field}")
                return False
        
        print("  Account statement generated successfully")
        print(f"  Statement period: {statement['statement_period']}")
        print(f"  Transaction count: {statement['transaction_count']}")
        return True
        
    def test_failed_login_tracking(self):
        """Test failed login attempt tracking"""
        # Try to login with incorrect password
        login_data = {
            "email": self.test_email,
            "password": "WrongPassword123"
        }
        
        # Make 3 failed login attempts
        for i in range(3):
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code != 401:
                print(f"  Expected status 401 for failed login, got {response.status_code}")
                return False
            
            self.failed_login_attempts += 1
            print(f"  Failed login attempt {self.failed_login_attempts} recorded")
        
        # Now try with correct password
        login_data["password"] = "Test123!"
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"  Expected status 200 for successful login, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        print("  Failed login tracking works correctly")
        return True
        
    def test_admin_analytics(self):
        """Test admin analytics dashboard"""
        if not self.admin_token:
            print("  Admin token not available")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{self.base_url}/admin/analytics", headers=headers)
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        if "analytics" not in data:
            print("  Missing analytics in response")
            return False
        
        analytics = data["analytics"]
        
        # Verify analytics contains required sections
        required_sections = ["users", "accounts", "transactions"]
        for section in required_sections:
            if section not in analytics:
                print(f"  Missing required section in analytics: {section}")
                return False
        
        # Verify user stats
        if "total" not in analytics["users"] or "active" not in analytics["users"]:
            print("  Missing user statistics")
            return False
            
        # Verify account stats
        if "total" not in analytics["accounts"] or "total_balance" not in analytics["accounts"]:
            print("  Missing account statistics")
            return False
            
        # Verify transaction stats
        if "total" not in analytics["transactions"] or "total_volume" not in analytics["transactions"]:
            print("  Missing transaction statistics")
            return False
        
        print("  Admin analytics dashboard works correctly")
        print(f"  Total users: {analytics['users']['total']}")
        print(f"  Total accounts: {analytics['accounts']['total']}")
        print(f"  Total transactions: {analytics['transactions']['total']}")
        return True
        
    def test_user_status_management(self):
        """Test user status management by admin"""
        if not self.admin_token or not self.customer_user_id:
            print("  Admin token or customer user ID not available")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Deactivate user
        status_data = {
            "user_id": self.customer_user_id,
            "status": "inactive"
        }
        
        response = requests.post(f"{self.base_url}/admin/users/status", json=status_data, headers=headers)
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        # Verify user can't login when inactive
        login_data = {
            "email": self.test_email,
            "password": "Test123!"
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        if response.status_code != 401:
            print(f"  Expected status 401 for inactive user login, got {response.status_code}")
            return False
        
        # Reactivate user
        status_data["status"] = "active"
        response = requests.post(f"{self.base_url}/admin/users/status", json=status_data, headers=headers)
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        # Verify user can login again
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"  Expected status 200 for reactivated user login, got {response.status_code}")
            return False
        
        print("  User status management works correctly")
        return True
        
    def test_bulk_operations(self):
        """Test bulk operations (interest/fees)"""
        if not self.admin_token:
            print("  Admin token not available")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.post(f"{self.base_url}/admin/bulk-operations", headers=headers)
        
        if response.status_code != 200:
            print(f"  Expected status 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        if "interest_applied" not in data or "fees_applied" not in data:
            print("  Missing bulk operation results in response")
            return False
        
        print("  Bulk operations completed successfully")
        print(f"  Interest applied to {data['interest_applied']} accounts")
        print(f"  Fees applied to {data['fees_applied']} accounts")
        return True
        
    def test_transfer_limits(self):
        """Test transfer limits"""
        if not self.customer_token or not self.customer_accounts or len(self.customer_accounts) < 2:
            print("  Not enough accounts to test transfer limits")
            return False
        
        from_account = self.customer_accounts[0]
        to_account = self.customer_accounts[1]
        
        # Try to transfer more than the limit (10,000)
        transfer_data = {
            "from_account_id": from_account["account_id"],
            "to_account_id": to_account["account_id"],
            "amount": 15000.0,
            "transfer_type": "internal",
            "description": "Test transfer limit"
        }
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.post(f"{self.base_url}/transfers", json=transfer_data, headers=headers)
        
        # Should fail with 400 Bad Request
        if response.status_code != 400:
            print(f"  Expected status 400 for over-limit transfer, got {response.status_code}")
            return False
        
        print("  Transfer limits enforced correctly")
        return True

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n=== BANKING API TESTS ===\n")
        
        # Run tests in sequence
        self.run_test("Health Check", self.test_health_check)
        self.run_test("Register Customer", self.test_register_customer)
        self.run_test("Login Admin", self.test_login_admin)
        self.run_test("Get Customer Accounts", self.test_get_customer_accounts)
        self.run_test("Internal Transfer", self.test_internal_transfer)
        self.run_test("Admin Credit Account", self.test_admin_credit_account)
        
        # Enhanced feature tests
        self.run_test("Transaction Filtering", self.test_transaction_filtering)
        self.run_test("Account Statement", self.test_account_statement)
        self.run_test("Failed Login Tracking", self.test_failed_login_tracking)
        self.run_test("Admin Analytics", self.test_admin_analytics)
        self.run_test("User Status Management", self.test_user_status_management)
        self.run_test("Bulk Operations", self.test_bulk_operations)
        self.run_test("Transfer Limits", self.test_transfer_limits)
        
        # Print summary
        print("\n=== TEST SUMMARY ===")
        print(f"Tests passed: {self.tests_passed}/{self.tests_run} ({self.tests_passed/self.tests_run*100:.1f}%)")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = BankingAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)