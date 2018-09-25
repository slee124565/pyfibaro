
import requests

payload = {
    "scene_name": "environmental information",
    "lang_code": "en"
    }

# r = requests.post('http://flhshowroom.mynetgear.com:8000/vb/i/s/',
#                   json=payload)


payload = {
    's': 'reading mode',
    'c': 'en',
    'k': 'test'
    }
r = requests.get('http://flhshowroom.mynetgear.com:8000/vb/i/s/',
                  params=payload)
