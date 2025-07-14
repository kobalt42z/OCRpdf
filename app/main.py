from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
import tempfile
import os
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageDraw
import ocrmypdf

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

@app.post("/ocr/pdf-overlay")
async def ocr_pdf_overlay(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
        tmp_in.write(await file.read())
        tmp_in_path = tmp_in.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
        tmp_out_path = tmp_out.name
    # Run OCRmyPDF to add a text layer for Hebrew
    ocrmypdf.ocr(tmp_in_path, tmp_out_path, deskew=True, lang="heb")
    with open(tmp_out_path, "rb") as f:
        pdf_bytes = f.read()
    os.remove(tmp_in_path)
    os.remove(tmp_out_path)
    return StreamingResponse(iter([pdf_bytes]), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=ocr_overlay.pdf"})
