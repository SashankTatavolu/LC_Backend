import requests

register_url = 'http://localhost:5000/api/users/register'
login_url = 'http://localhost:5000/api/users/login'

data_register = {
    "username": "testuser1",
    "password": "testpassword",
    "role": "admin"
}


data_login = {
    "username": "testuser1",
    "password": "testpassword"
}


def test_api(url, data):
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Success: {response.json()}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error: {e}")

# print("Testing /register endpoint:")
test_api(register_url, data_register)

# print("\nTesting /get_ner_entities_sentence endpoint:")
test_api(login_url, data_login)