import requests
import sys

try:
    # 3. Google Login Mock
    response = requests.post('http://localhost:8000/api/auth/google/', json={
        'id_token': 'mock_google_token'
    })

    if response.status_code == 200:
        print("Google Mock Login Successful")
        print(response.json())
    else:
        print(f"Google Mock Login Failed: {response.status_code} {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"Connection Failed: {e}")
    sys.exit(1)
