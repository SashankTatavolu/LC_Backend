import requests

def get_jwt_token(username, password):
    login_url = "http://localhost:5000/api/users/login"  

    login_payload = {
        "username": username,
        "password": password
    }

    response = requests.post(login_url, json=login_payload)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Login failed.")
        return None

def test_add_multiple_sentences():
    jwt_token = get_jwt_token("testuser1", "testpassword")  
    print("token: ",jwt_token)

    if jwt_token:
        add_sentences_url = "http://localhost:5000/api/sentences/add"  

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "chapter_id": 3,  
            "sentences": [
                "This is sentence 1.",
                "This is sentence 2.",
                "This is sentence 3.",
                "This is sentence 4."
            ]
        }

        response = requests.post(add_sentences_url, headers=headers, json=payload)

        print("Response:", response.status_code)
        print(response.json())
    else:
        print("Unable to get JWT token. Test aborted.")

test_add_multiple_sentences()
