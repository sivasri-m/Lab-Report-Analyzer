!pip install fastapi uvicorn pyngrok python-multipart pillow pytesseract
!apt install tesseract-ocr

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import pytesseract
import io
import re
from pyngrok import ngrok
import nest_asyncio
import uvicorn

nest_asyncio.apply()

app = FastAPI()

def extract_tests_from_text(text: str):
    lab_tests = []
    pattern = re.compile(
        r'(?P<test_name>[A-Z\s\(\)\-]+?)\s+(?P<test_value>\d+\.?\d*)\s*(?P<test_unit>[a-zA-Z/%µ]*)\s+(?P<ref_range>\d+\.?\d*\s*[-–]\s*\d+\.?\d*)'
    )

    for match in pattern.finditer(text):
        test_name = match.group("test_name").strip()
        test_value = float(match.group("test_value"))
        test_unit = match.group("test_unit").strip()
        ref_range = match.group("ref_range").replace("–", "-").strip()
        ref_low, ref_high = map(float, re.split(r"[-–]", ref_range))

        lab_tests.append({
            "test_name": test_name,
            "test_value": str(test_value),
            "bio_reference_range": f"{ref_low}-{ref_high}",
            "test_unit": test_unit,
            "lab_test_out_of_range": not (ref_low <= test_value <= ref_high)
        })

    return lab_tests

@app.post("/get-lab-tests")
async def get_lab_tests(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        lab_tests = extract_tests_from_text(text)

        return JSONResponse(status_code=200, content={
            "is_success": True,
            "data": lab_tests
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "is_success": False,
            "error": str(e)
        })

!ngrok config add-authtoken 2wOG851HtrYLhMNS0sF6A20LfjN_659J165DqhFTBp9QJCaRh

from google.colab import files
import requests
from pyngrok import ngrok


uploaded = files.upload()


file_path = list(uploaded.keys())[0]

from threading import Thread

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

api_thread = Thread(target=run_api, daemon=True)
api_thread.start()

public_url = ngrok.connect(8000)
print(f"Public URL: {public_url}")

import requests
url = public_url.public_url + "/get-lab-tests"

with open(file_path, 'rb') as f:
    response = requests.post(url, files={'file': f})

print(response.json())