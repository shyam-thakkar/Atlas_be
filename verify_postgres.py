import requests
import sys

try:
    # 1. Signup
    response = requests.post('http://localhost:8000/api/auth/signup/', json={
        'email': 'postgres_test@example.com',
        'password': 'StrongPassword123'
    })
    
    if response.status_code == 201:
        print("Signup Successful")
    else:
        # If user already exists (from previous runs), that's also a success for DB connection
        if 'already exists' in str(response.content):
            print("Signup Successful (User exists)")
        else:
            print(f"Signup Failed: {response.status_code} {response.text}")
            sys.exit(1)

    # 2. Login
    response = requests.post('http://localhost:8000/api/auth/login/', json={
        'email': 'postgres_test@example.com',
        'password': 'StrongPassword123'
    })

    if response.status_code == 200:
        print("Login Successful")
    else:
        print(f"Login Failed: {response.status_code} {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"Connection Failed: {e}")
    sys.exit(1)
