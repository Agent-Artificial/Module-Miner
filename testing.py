import base64
import requests
import json
from typing import Dict, Any
from pydantic import BaseModel


class TranslationRequest(BaseModel):
    data: Dict[str, Any]


def send():
    infile = "modules/translation/in/audio_request.wav"
    outfile = "modules/translation/out/audio_request.txt"
    
    with open(infile, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")
    
    request = {
        "data": {
            "input": audio_data,
            "task_string": "speech2text",
            "source_language": "english",
            "target_language": "spanish"
        }
    }
    
    response = requests.post(
        "http://127.0.0.1:4269/modules/translation/process", json=request, timeout=30
    )
    print(response.text)


send()