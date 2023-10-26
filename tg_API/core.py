import requests

url = "https://hotels4.p.rapidapi.com/v2/get-meta-data"

headers = {
    "X-RapidAPI-Key": "6c0112302amshcbee9b2549c2ba5p1a1ed6jsn6bec4127b925",
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}

response = requests.get(url, headers=headers)

#print(response.json())
