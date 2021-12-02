import cv2
from fastapi import Request, FastAPI
import numpy as np
import base64
from compute import predict
from fuzzy import fuzzy
from cachetools import TTLCache
import uuid
import json
import random

cache = TTLCache(maxsize=float('inf'), ttl=10800)
app = FastAPI()


@ app.post("/analyze")
async def analyze(request: Request):
    try:
        json = await request.json()
        buffer = base64.b64decode(json['payload'])
        array = np.fromstring(buffer, dtype=np.uint8)
        img = cv2.imdecode(array, cv2.IMREAD_COLOR)
        face_analyze = predict(img)

        if face_analyze is None:
            return {
                "success": True,
                "message": "Your face is not detected in your image. Please try again"
            }

        id = str(uuid.uuid4())

        cache[id] = {
            "done": False,
            "data": face_analyze,
        }
        return {
            "success": True,
            "id": id
        }
    except:
        return {
            "success": False,
            "message": "The request is malformed. Please try again"
        }


@ app.post("/submit")
async def submit(request: Request):
    try:
        json = await request.json()
        id = json["id"]
        scores = json["scores"]

        if (type(id) != str or type(scores) != list or len(scores) != 4):
            return {
                "success": False,
                "message": "The request is malformed. Please try again"
            }

        if id not in cache:
            return {
                "success": False,
                "message": "This ID is not available"
            }

        el = cache[id]

        if el['done'] is True:
            return {
                "success": False,
                "message": "This ID is not available"
            }

        face_analyze = el['data']
        result = []

        for i in range(0, len(scores)):
            result.append(fuzzy(face_analyze[i], scores[i]))

        cache[id] = {
            "done": True,
            "data": result,
        }

        return {
            "success": True,
            "result": result
        }
    except:
        return {
            "success": False,
            "message": "The request is malformed. Please try again"
        }


@ app.get("/view/{id}")
async def view(id: str):
    try:
        if id not in cache:
            return {
                "success": False,
                "message": "This ID is not available"
            }
        el = cache[id]

        if el['done'] is False:
            return {
                "success": False,
                "message": "This ID is not available"
            }
        return {
            "success": True,
            "result": el['data']
        }

    except:
        return {
            "success": False,
            "message": "The request is malformed. Please try again"
        }


def read_to_json(filename):
    with open(filename, 'r') as data_file:
        json_data = data_file.read()
    return json.loads(json_data)


it = read_to_json('../quizs/it.json')
business = read_to_json('../quizs/business.json')
graphics = read_to_json('../quizs/graphics.json')
language = read_to_json('../quizs/language.json')

num_of_question = 3


@ app.get("/quiz")
async def quiz():
    result = []

    temp = it
    random.shuffle(temp)
    for i in range(num_of_question):
        result.append({
            'content': temp[i],
            'type': 'it'
        })

    temp = business
    random.shuffle(temp)
    for i in range(num_of_question):
        result.append({
            'content': temp[i],
            'type': 'business'
        })

    temp = graphics
    random.shuffle(temp)
    for i in range(num_of_question):
        result.append({
            'content': temp[i],
            'type': 'graphics'
        })

    temp = language
    random.shuffle(temp)
    for i in range(num_of_question):
        result.append({
            'content': temp[i],
            'type': 'language'
        })

    return result