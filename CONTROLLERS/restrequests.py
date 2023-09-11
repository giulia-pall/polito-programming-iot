import requests

def perform_get_request(url):
    try:
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # If the response contains JSON data, you can access it like this:
            json_data = response.json()
            return json_data
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None
        
def perform_post_request(url, data):
    try:
        response = requests.post(url, json=data)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # If the response contains JSON data, you can access it like this:
            json_data = response.json()
            return json_data
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

