from fastapi import FastAPI, File, UploadFile
import openpyxl

app = FastAPI()

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    try:
        workbook = openpyxl.load_workbook(file.file)
        sheet_names = workbook.sheetnames
        print(f"Received file: {file.filename}")
        return {"message": "success"}
    except Exception as e:
        return {"error": str(e)}
