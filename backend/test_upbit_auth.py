#!/usr/bin/env python3
"""
Test script to verify Upbit API authentication
"""
import os
import jwt
import uuid
import hashlib
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_upbit_auth():
    """Test Upbit API authentication"""
    
    # Get credentials from environment
    access_key = os.getenv('UPBIT_ACCESS_KEY')
    secret_key = os.getenv('UPBIT_SECRET_KEY')
    
    print(f"Access Key present: {bool(access_key)}")
    print(f"Secret Key present: {bool(secret_key)}")
    
    if not access_key or not secret_key:
        print("\nERROR: API keys not found in environment variables!")
        print("Please set UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY in .env file")
        return
    
    # Check key format
    print(f"\nAccess Key length: {len(access_key)}")
    print(f"Secret Key length: {len(secret_key)}")
    print(f"Access Key starts with: {access_key[:8]}...")
    
    # Generate JWT token
    payload = {
        'access_key': access_key,
        'nonce': str(uuid.uuid4()),
    }
    
    jwt_token = jwt.encode(payload, secret_key, algorithm='HS256')
    headers = {'Authorization': f'Bearer {jwt_token}'}
    
    print(f"\nJWT Token generated: {jwt_token[:50]}...")
    
    # Test API call
    url = "https://api.upbit.com/v1/accounts"
    print(f"\nTesting API call to: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\n✅ Authentication successful!")
            accounts = response.json()
            print(f"Found {len(accounts)} accounts:")
            for acc in accounts:
                print(f"  - {acc['currency']}: {acc['balance']} (locked: {acc['locked']})")
        else:
            print(f"\n❌ Authentication failed!")
            print(f"Response: {response.text}")
            
            # Common issues
            if 'invalid_access_key' in response.text:
                print("\nPossible issues:")
                print("1. Access key is incorrect or expired")
                print("2. Access key has wrong format")
                print("3. Check if keys are from the correct Upbit account")
            elif 'jwt_verification_error' in response.text:
                print("\nPossible issues:")
                print("1. Secret key is incorrect")
                print("2. JWT encoding issue")
                
    except Exception as e:
        print(f"\n❌ Error during API call: {e}")

if __name__ == "__main__":
    test_upbit_auth()