from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
import jwt
import hashlib
import uuid
from typing import Optional, List
import secrets

app = FastAPI(title="Demo Banking API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.demo_banking

# JWT settings
JWT_SECRET = "demo_banking_secret_key_2025"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str
    address: str
    date_of_birth: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: Optional[str] = None
    to_email: Optional[str] = None
    amount: float
    transfer_type: str  # wire, domestic, internal
    description: str
    recipient_name: Optional[str] = None
    recipient_bank: Optional[str] = None
    routing_number: Optional[str] = None

class AdminCreditDebit(BaseModel):
    account_id: str
    amount: float
    transaction_type: str  # credit or debit
    description: str
    backdate: Optional[str] = None

class Account(BaseModel):
    account_id: str
    account_type: str
    balance: float
    status: str

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_jwt_token(user_data: dict) -> str:
    payload = {
        "user_id": user_data["user_id"],
        "email": user_data["email"],
        "role": user_data["role"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    user = db.users.find_one({"user_id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def generate_account_number() -> str:
    return str(secrets.randbelow(9000000000) + 1000000000)

def create_user_accounts(user_id: str):
    accounts = [
        {
            "account_id": str(uuid.uuid4()),
            "user_id": user_id,
            "account_number": generate_account_number(),
            "account_type": "checking",
            "balance": 1000.00,  # Demo starting balance
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "account_id": str(uuid.uuid4()),
            "user_id": user_id,
            "account_number": generate_account_number(),
            "account_type": "savings",
            "balance": 5000.00,  # Demo starting balance
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    result = db.accounts.insert_many(accounts)
    
    # Add _id to each account
    for i, account_id in enumerate(result.inserted_ids):
        accounts[i]["_id"] = str(account_id)
        
    return accounts

def create_transaction(transaction_data: dict):
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        **transaction_data,
        "created_at": datetime.utcnow()
    }
    db.transactions.insert_one(transaction)
    return transaction

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    # Check if user already exists
    existing_user = db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    user = {
        "user_id": user_id,
        "email": user_data.email,
        "password": hashed_password,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone": user_data.phone,
        "address": user_data.address,
        "date_of_birth": user_data.date_of_birth,
        "role": "customer",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    db.users.insert_one(user)
    
    # Create default accounts
    accounts = create_user_accounts(user_id)
    
    # Convert ObjectId to string for all accounts
    for account in accounts:
        if "_id" in account:
            account["_id"] = str(account["_id"])
    
    # Generate JWT token
    token = create_jwt_token(user)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "user_id": user_id,
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "role": "customer"
        },
        "accounts": accounts
    }

@app.post("/api/auth/login")
async def login_user(login_data: UserLogin):
    user = db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user["status"] != "active":
        raise HTTPException(status_code=401, detail="Account is inactive")
    
    token = create_jwt_token(user)
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "role": user["role"]
        }
    }

@app.get("/api/accounts")
async def get_user_accounts(current_user = Depends(get_current_user)):
    accounts = list(db.accounts.find(
        {"user_id": current_user["user_id"]}
    ))
    
    # Convert ObjectId to string to make it JSON serializable
    for account in accounts:
        if "_id" in account:
            account["_id"] = str(account["_id"])
    
    return {"accounts": accounts}

@app.get("/api/accounts/{account_id}/transactions")
async def get_account_transactions(account_id: str, current_user = Depends(get_current_user)):
    # Verify account ownership or admin access
    account = db.accounts.find_one({"account_id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if current_user["role"] not in ["admin", "super_admin"] and account["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transactions = list(db.transactions.find(
        {"$or": [{"from_account_id": account_id}, {"to_account_id": account_id}]}
    ).sort("created_at", -1).limit(50))
    
    # Convert ObjectId to string to make it JSON serializable
    for transaction in transactions:
        if "_id" in transaction:
            transaction["_id"] = str(transaction["_id"])
    
    return {"transactions": transactions}

@app.post("/api/transfers")
async def create_transfer(transfer_data: TransferRequest, current_user = Depends(get_current_user)):
    # Verify source account ownership
    from_account = db.accounts.find_one({"account_id": transfer_data.from_account_id})
    if not from_account or from_account["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Invalid source account")
    
    # Check sufficient balance
    if from_account["balance"] < transfer_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Handle different transfer types
    if transfer_data.transfer_type == "internal":
        # Internal transfer between user's own accounts
        to_account = db.accounts.find_one({"account_id": transfer_data.to_account_id})
        if not to_account or to_account["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=400, detail="Invalid destination account")
        
        # Update balances
        db.accounts.update_one(
            {"account_id": transfer_data.from_account_id},
            {"$inc": {"balance": -transfer_data.amount}, "$set": {"updated_at": datetime.utcnow()}}
        )
        db.accounts.update_one(
            {"account_id": transfer_data.to_account_id},
            {"$inc": {"balance": transfer_data.amount}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        # Create transaction record
        transaction = create_transaction({
            "from_account_id": transfer_data.from_account_id,
            "to_account_id": transfer_data.to_account_id,
            "amount": transfer_data.amount,
            "transfer_type": transfer_data.transfer_type,
            "description": transfer_data.description,
            "status": "completed",
            "user_id": current_user["user_id"]
        })
    
    elif transfer_data.transfer_type in ["wire", "domestic"]:
        # External transfer (simulated)
        # Update source account balance
        db.accounts.update_one(
            {"account_id": transfer_data.from_account_id},
            {"$inc": {"balance": -transfer_data.amount}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        # Create transaction record
        transaction = create_transaction({
            "from_account_id": transfer_data.from_account_id,
            "to_account_id": None,
            "amount": transfer_data.amount,
            "transfer_type": transfer_data.transfer_type,
            "description": transfer_data.description,
            "recipient_name": transfer_data.recipient_name,
            "recipient_bank": transfer_data.recipient_bank,
            "routing_number": transfer_data.routing_number,
            "status": "pending" if transfer_data.transfer_type == "wire" else "completed",
            "user_id": current_user["user_id"]
        })
    
    # Convert ObjectId to string
    if "_id" in transaction:
        transaction["_id"] = str(transaction["_id"])
    
    return {
        "message": "Transfer initiated successfully",
        "transaction": transaction
    }

# Admin routes
@app.get("/api/admin/users")
async def get_all_users(current_user = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = list(db.users.find({}, {"password": 0}))
    
    # Convert ObjectId to string to make it JSON serializable
    for user in users:
        if "_id" in user:
            user["_id"] = str(user["_id"])
    
    return {"users": users}

@app.get("/api/admin/accounts")
async def get_all_accounts(current_user = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "user_info"
            }
        },
        {
            "$unwind": "$user_info"
        },
        {
            "$project": {
                "account_id": 1,
                "account_number": 1,
                "account_type": 1,
                "balance": 1,
                "status": 1,
                "user_name": {"$concat": ["$user_info.first_name", " ", "$user_info.last_name"]},
                "user_email": "$user_info.email",
                "created_at": 1
            }
        }
    ]
    
    accounts = list(db.accounts.aggregate(pipeline))
    
    # Convert ObjectId to string to make it JSON serializable
    for account in accounts:
        if "_id" in account:
            account["_id"] = str(account["_id"])
    
    return {"accounts": accounts}

@app.post("/api/admin/credit-debit")
async def admin_credit_debit(transaction_data: AdminCreditDebit, current_user = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    account = db.accounts.find_one({"account_id": transaction_data.account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Handle credit/debit
    amount_change = transaction_data.amount if transaction_data.transaction_type == "credit" else -transaction_data.amount
    
    # Check for sufficient funds in case of debit
    if transaction_data.transaction_type == "debit" and account["balance"] < transaction_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds for debit")
    
    # Update account balance
    db.accounts.update_one(
        {"account_id": transaction_data.account_id},
        {"$inc": {"balance": amount_change}, "$set": {"updated_at": datetime.utcnow()}}
    )
    
    # Create transaction record with optional backdating
    transaction_date = datetime.utcnow()
    if transaction_data.backdate and current_user["role"] == "super_admin":
        try:
            transaction_date = datetime.fromisoformat(transaction_data.backdate)
        except ValueError:
            pass  # Use current date if invalid backdate
    
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "from_account_id": None if transaction_data.transaction_type == "credit" else transaction_data.account_id,
        "to_account_id": transaction_data.account_id if transaction_data.transaction_type == "credit" else None,
        "amount": transaction_data.amount,
        "transfer_type": "admin_" + transaction_data.transaction_type,
        "description": transaction_data.description,
        "status": "completed",
        "admin_user_id": current_user["user_id"],
        "created_at": transaction_date,
        "backdated": transaction_data.backdate is not None
    }
    
    db.transactions.insert_one(transaction)
    
    return {
        "message": f"Account {transaction_data.transaction_type} successful",
        "transaction": transaction
    }

@app.get("/api/admin/transactions")
async def get_all_transactions(current_user = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    transactions = list(db.transactions.find({}).sort("created_at", -1).limit(100))
    
    # Convert ObjectId to string to make it JSON serializable
    for transaction in transactions:
        if "_id" in transaction:
            transaction["_id"] = str(transaction["_id"])
    
    return {"transactions": transactions}

# Create admin user on startup
@app.on_event("startup")
async def create_admin_user():
    admin_email = "admin@demobank.com"
    admin_user = db.users.find_one({"email": admin_email})
    
    if not admin_user:
        admin_id = str(uuid.uuid4())
        admin = {
            "user_id": admin_id,
            "email": admin_email,
            "password": hash_password("admin123"),
            "first_name": "Bank",
            "last_name": "Administrator",
            "phone": "555-0001",
            "address": "123 Bank Street, Financial District",
            "date_of_birth": "1980-01-01",
            "role": "super_admin",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        db.users.insert_one(admin)
        print(f"Created admin user: {admin_email} / admin123")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)