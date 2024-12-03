import requests

url = "http://127.0.0.1:5000/computer_use/" 

payload = {
    "instruction": " Go to google.com and search for movie 'Fight club' and return the lead actors in a JSON"
}

try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Success:", response.json())
    else:
        print("Error:", response.status_code, response.json())
except Exception as e:
    print(f"Error sending request: {e}")