import requests

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {"Content-Type": "application/json"}
data = {
    "model": "mistralai/mistral-7b-instruct:free",
    "messages": [{"role": "user", "content": "hello"}]
}
try:
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code)
    print(response.text)
except Exception as e:
    print(e)
