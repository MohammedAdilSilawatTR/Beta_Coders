from fastapi import FastAPI, File, UploadFile, Form
import openpyxl
import json
from openai import OpenAI
import os # For API Key
from dotenv import load_dotenv
from datetime import datetime # Added for datetime conversion

app = FastAPI()

# Initialize OpenAI client - Assumes OPENAI_API_KEY environment variable is set
# You might want to add more robust error handling for API key loading in a production app
try:
    load_dotenv()  # Load environment variables from .env file if it exists
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                    base_url="https://litellm.int.thomsonreuters.com")
except TypeError:
    print("ERROR: OPENAI_API_KEY environment variable not set.")
    client = None # Or handle this more gracefully

PREDEFINED_COLUMNS = ["amount", "transactionDate", "transactionDescription", "disallowableExpenses"]
MAX_SAMPLE_ROWS = 5 # Number of sample data rows to send to LLM for each column

def convert_datetimes_to_string(obj):
    """
    Recursively convert datetime objects in nested lists/dictionaries to ISO format strings.
    """
    if isinstance(obj, list):
        return [convert_datetimes_to_string(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_datetimes_to_string(v) for k, v in obj.items()}
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

@app.post("/uploadfile/")
async def create_upload_file(
    file: UploadFile = File(...),
    business_description: str = Form("") 
):
    try:
        print(f"Received file: {file.filename}")
        print(f"Received Business Description: {business_description}")
        workbook = openpyxl.load_workbook(file.file)
        
        sheet = workbook.active
        
        non_empty_columns_indexes = [
            i for i, col in enumerate(sheet.iter_cols(values_only=True))
            if any(cell is not None for cell in col)
        ]

        actual_headers = []
        processed_data_rows = []
        header_row_found_excel_idx = -1 # 1-based index of the header row in Excel

        if not non_empty_columns_indexes:
            print("Warning: No non-empty columns found. Headers and data rows will be empty.")
        else:
            for current_excel_row_idx, row_tuple in enumerate(sheet.iter_rows(values_only=True), start=1):
                # Extract values from the current row based on non_empty_columns_indexes
                current_row_selected_cols = []
                for col_idx in non_empty_columns_indexes:
                    if col_idx < len(row_tuple):
                        current_row_selected_cols.append(row_tuple[col_idx])
                    else:
                        current_row_selected_cols.append(None) 
                
                # Check if this row (after selecting relevant columns) has any content
                if any(cell_value is not None for cell_value in current_row_selected_cols):
                    if header_row_found_excel_idx == -1: # Header not yet found
                        actual_headers = [str(h) if h is not None else f"Unknown_Header_{i}" 
                                          for i, h in enumerate(current_row_selected_cols)]
                        header_row_found_excel_idx = current_excel_row_idx
                        print(f"Header row found at Excel row index: {header_row_found_excel_idx}")
                    else: # Header already found, this is a data row
                        processed_data_rows.append(current_row_selected_cols)
            
            if header_row_found_excel_idx == -1:
                print("Warning: No non-empty row found to be used as header. Headers and data will be empty.")

        print(f"Sheet Name: {sheet.title}")
        print(f"Actual Headers: {actual_headers}")
        # print(f"Processed Data Rows (first few): {processed_data_rows[:5]}") # Print first 5 for brevity
        if header_row_found_excel_idx != -1 and not processed_data_rows:
            print("Info: Header row found, but no subsequent data rows.")

        header_mapping = {}
        # Use actual_headers for the condition and further processing
        if client and actual_headers: 
            # Prepare sample data for LLM using actual_headers and processed_data_rows
            raw_sample_data_for_llm = {}
            for i, header_name in enumerate(actual_headers):
                column_data = [row[i] for row in processed_data_rows if i < len(row) and row[i] is not None]
                raw_sample_data_for_llm[header_name] = column_data[:MAX_SAMPLE_ROWS]
            
            # Convert datetimes in sample data before sending to LLM
            sample_data_for_llm = convert_datetimes_to_string(raw_sample_data_for_llm)
            print(f"Sample data for LLM (datetimes converted): {sample_data_for_llm}")

            # Construct prompt for OpenAI
            prompt_messages = [
                {
                    "role": "system",
                    "content": "You are an expert data mapping assistant. Your task is to map user-provided Excel column headers to a predefined list of standard column names. You will be given the user's headers, sample data from each of their columns, and the list of predefined standard columns. Return your mapping as a JSON object where keys are the predefined standard columns and values are the matched user headers. If no good match is found for a user header, use null as its value."
                },
                {
                    "role": "user",
                    "content": f"""
User Headers:
{actual_headers}

Sample Data per User Header (first {MAX_SAMPLE_ROWS} non-null values):
{json.dumps(sample_data_for_llm, indent=2)}

Predefined Standard Columns:
{PREDEFINED_COLUMNS}

Please provide the mapping as a JSON object.
"""
                }
            ]

            try:
                print("Sending request to OpenAI...")
                chat_completion = client.chat.completions.create(
                    messages=prompt_messages,
                    model="openai/gpt-4o", # Or "gpt-4" or other preferred model
                    response_format={ "type": "json_object" } # Request JSON output
                )
                llm_response_content = chat_completion.choices[0].message.content
                print(f"LLM raw response: {llm_response_content}")
                if llm_response_content:
                    header_mapping = json.loads(llm_response_content)
                else:
                    # Fallback using actual_headers
                    header_mapping = {header: None for header in actual_headers} 
                    print("LLM returned empty content.")

            except Exception as llm_e:
                print(f"Error calling OpenAI or parsing response: {llm_e}")
                # Fallback: create a null mapping if LLM fails
                header_mapping = {header: None for header in actual_headers}
        
        elif not client:
            print("OpenAI client not initialized. Skipping LLM mapping.")
            # Fallback using actual_headers
            header_mapping = {header: "OpenAI client not initialized" for header in actual_headers}


        # Convert datetimes in processed_data_rows before returning
        final_processed_data_rows = convert_datetimes_to_string(processed_data_rows)

        return {
            "filename": file.filename,
            "headers": actual_headers, # Use actual_headers
            "non_empty_rows": final_processed_data_rows, # Use the correctly processed data rows
            "header_mapping": header_mapping
        }
    except Exception as e:
        print(f"Error in file processing: {e}")
        return {"error": str(e), "details": "Error during file processing or LLM interaction."}
