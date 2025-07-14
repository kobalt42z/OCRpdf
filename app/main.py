from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import tempfile
import os
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

app = FastAPI()

@app.post("/ocr")
async def ocr_pdf(file: UploadFile = File(...)):
    # Save uploaded PDF to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    # Convert PDF pages to images
    images = convert_from_path(tmp_path)
    result = []
    for page_num, img in enumerate(images):
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        page_result = []
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            if ocr_data['text'][i].strip():
                page_result.append({
                    'text': ocr_data['text'][i],
                    'left': ocr_data['left'][i],
                    'top': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i],
                    'conf': ocr_data['conf'][i]
                })
        result.append({'page': page_num + 1, 'items': page_result})
    os.remove(tmp_path)
    return JSONResponse(content={'pages': result})
