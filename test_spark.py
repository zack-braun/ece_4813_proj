import requests

params = {
        'Tavg': 73,
        'Tmin': 66,
        'Tmax': 80,
        'Depart': 2,
        'PrecipTotal': 1.11,
        'Heat': 0
        }

requests.get("http://192.168.10.101:8081/kmeans/6", params=params)
