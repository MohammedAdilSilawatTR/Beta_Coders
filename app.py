from fastapi import FastAPI, File, UploadFile
import openpyxl

app = FastAPI()

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    try:
        print(f"Received file: {file.filename}")
        workbook = openpyxl.load_workbook(file.file)
        
        sheet = workbook.active
        
        non_empty_columns_indexes = [
            i for i, col in enumerate(sheet.iter_cols(values_only=True))
            if any(cell is not None for cell in col)
        ]
        
        headers = [sheet.cell(row=1, column=i+1).value for i in non_empty_columns_indexes]
        
        non_empty_rows = [
            [row[i] for i in non_empty_columns_indexes]
            for row in sheet.iter_rows(min_row=2, values_only=True)
            if any(row[i] is not None for i in non_empty_columns_indexes)
        ]
        
        print(f"Headers: {headers}")
        print(f"Non-empty rows: {non_empty_rows}")

        return {"filename": file.filename, "headers": headers, "non_empty_rows": non_empty_rows}
    except Exception as e:
        return {"error": str(e)}