import requests
from pprint import pprint

base_url = 'https://canvas.iiit.ac.in/lc/api/chapters'
register_url = f'{base_url}/add'
get_chapters_url = f'{base_url}/by_project/'

chapter_data = {
    "project_id": 2,
    "name": "Chapter 1",
    "text": "This is the text for Chapter 1"
}

project_id = 1  

def get_jwt_token():
    try:
        login_url = 'https://canvas.iiit.ac.in/lc/api/users/login'
        data_login = {
            "username": "testuser1",
            "password": "testpassword"
        }
        response = requests.post(login_url, json=data_login)
        if response.status_code == 200:
            token = response.json()['access_token']
            return token
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_add_chapter(token):
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(register_url, json=chapter_data, headers=headers)
        if response.status_code == 201:
            data = response.json()
            print("Chapter added successfully:")
            pprint(data)
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_get_chapters(token):
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{get_chapters_url}/{project_id}", headers=headers)
        if response.status_code == 200:
            chapters_data = response.json()
            print("Chapters retrieved successfully:")
            pprint(chapters_data)
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error: {e}")

token = get_jwt_token()
if token:
    print("Testing add_chapter endpoint:")
    test_add_chapter(token)

    print("\nTesting get_chapters endpoint:")
    test_get_chapters(token)
else:
    print("Failed to obtain JWT token.")
