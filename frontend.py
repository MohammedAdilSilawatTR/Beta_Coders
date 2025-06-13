import streamlit as st
import requests
import pandas as pd # Import pandas for DataFrame
import json # Added import
import json

st.set_page_config(page_title="Smart AI Mapping", page_icon="🤖", layout="wide")

st.title("Excel File Uploader")

# Initialize session state variables if they don't exist
if 'business_description' not in st.session_state:
    st.session_state.business_description = ""
if 'transformed_data_for_table' not in st.session_state:
    st.session_state.transformed_data_for_table = []
if 'original_excel_headers' not in st.session_state:
    st.session_state.original_excel_headers = []
if 'llm_header_mapping' not in st.session_state:
    st.session_state.llm_header_mapping = {}
if 'df_display' not in st.session_state:
    st.session_state.df_display = pd.DataFrame()
if 'df_categorized_display' not in st.session_state: # New session state for categorized table
    st.session_state.df_categorized_display = pd.DataFrame()
if 'data_rows' not in st.session_state: # to store raw data_rows from uploadfile
    st.session_state.data_rows = []


# Add a text input for business description, bound to session state
st.session_state.business_description = st.text_input(
    "Enter Business Description (essential for categorization)", 
    value=st.session_state.business_description
)

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    if st.button("Upload and Map Headers"):
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        # Prepare data payload for form fields, using business_description from session state
        data = {"business_description": st.session_state.business_description}

        try:
            with st.spinner("Processing file and mapping headers..."):
                response = requests.post("http://localhost:8000/uploadfile/", files=files, data=data)
            
            if response.status_code == 200:
                st.success("File processed successfully!")
                
                response_data = response.json()
                # Store in session state
                st.session_state.original_excel_headers = response_data.get("headers", []) 
                st.session_state.data_rows = response_data.get("non_empty_rows", []) 
                st.session_state.llm_header_mapping = response_data.get("header_mapping", {})

                st.subheader("LLM Header Mapping Received:")
                st.json(st.session_state.llm_header_mapping)

                if not st.session_state.data_rows:
                    st.info("No data rows received from backend to display.")
                    st.session_state.transformed_data_for_table = []
                    st.session_state.df_display = pd.DataFrame()
                elif not st.session_state.original_excel_headers:
                    st.info("No original headers received from backend.")
                    st.session_state.transformed_data_for_table = []
                    st.session_state.df_display = pd.DataFrame()
                elif not st.session_state.llm_header_mapping or not any(st.session_state.llm_header_mapping.values()):
                    st.info("No valid header mapping received from LLM, or LLM could not map any headers.")
                    st.session_state.transformed_data_for_table = []
                    st.session_state.df_display = pd.DataFrame()
                else:
                    original_header_to_index = {header: i for i, header in enumerate(st.session_state.original_excel_headers)}
                    final_table_columns = list(st.session_state.llm_header_mapping.keys())
                    
                    temp_transformed_data = []
                    for row_values in st.session_state.data_rows:
                        new_mapped_row = {}
                        for predefined_col_name in final_table_columns:
                            original_excel_header_for_this_predefined_col = st.session_state.llm_header_mapping.get(predefined_col_name)
                            if original_excel_header_for_this_predefined_col and \
                               original_excel_header_for_this_predefined_col in original_header_to_index:
                                idx_in_original_row = original_header_to_index[original_excel_header_for_this_predefined_col]
                                if idx_in_original_row < len(row_values):
                                    new_mapped_row[predefined_col_name] = row_values[idx_in_original_row]
                                else:
                                    new_mapped_row[predefined_col_name] = None 
                            else:
                                new_mapped_row[predefined_col_name] = None 
                        temp_transformed_data.append(new_mapped_row)
                    
                    st.session_state.transformed_data_for_table = temp_transformed_data

                    if st.session_state.transformed_data_for_table:
                        df = pd.DataFrame(st.session_state.transformed_data_for_table)
                        date_column_name = "transactionDate"
                        if date_column_name in df.columns:
                            df[date_column_name] = pd.to_datetime(df[date_column_name], errors='coerce')
                            if pd.api.types.is_datetime64_any_dtype(df[date_column_name]):
                                df[date_column_name] = df[date_column_name].dt.strftime('%d/%m/%Y').fillna('')
                        
                        st.session_state.df_display = df # Store dataframe in session state
                    else:
                        st.info("Could not transform data for table display (e.g., mapping issues led to empty data).")
                        st.session_state.df_display = pd.DataFrame()
            else:
                st.error(f"Failed to process file: {response.status_code} - {response.text}")
                st.session_state.transformed_data_for_table = []
                st.session_state.df_display = pd.DataFrame()

        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to backend: {e}")
            st.session_state.transformed_data_for_table = []
            st.session_state.df_display = pd.DataFrame()
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            st.session_state.transformed_data_for_table = []
            st.session_state.df_display = pd.DataFrame()

# This section is now outside the "Upload and Map Headers" button's conditional block
# It will run on every script rerun, displaying data if it exists in session_state

if not st.session_state.df_display.empty:
    st.subheader("Mapped Data Table:")
    # Ensure columns are displayed in the order derived from LLM mapping keys plus 'Category' if it exists
    llm_cols = list(st.session_state.llm_header_mapping.keys())
    display_df_cols = [col for col in llm_cols if col in st.session_state.df_display.columns]
    if 'Category' in st.session_state.df_display.columns and 'Category' not in display_df_cols:
        display_df_cols.append('Category') # Add Category column if it exists and not already included

    if display_df_cols:
        st.dataframe(st.session_state.df_display[display_df_cols])
    else:
        # This case should ideally not be hit if df_display is not empty,
        # but as a fallback:
        st.dataframe(st.session_state.df_display)


    # Add "Categorize Transactions" button
    if st.button("Categorize Transactions"):
        if not st.session_state.business_description.strip():
            st.warning("Please enter a business description for categorization.")
        elif not st.session_state.transformed_data_for_table: 
            st.warning("No mapped transaction data available to categorize.")
        else:
            payload = {
                "business_description": st.session_state.business_description,
                "mapped_transactions": st.session_state.transformed_data_for_table 
            }
            try:
                with st.spinner("Categorizing transactions..."):
                    categorize_response = requests.post("http://localhost:8000/categorize-transactions/", json=payload)
                
                if categorize_response.status_code == 200:
                    st.success("Transactions categorized successfully!")
                    try:
                        categorized_data = categorize_response.json()
                    except json.JSONDecodeError as json_e:
                        st.error(f"Failed to parse JSON response from backend: {json_e}")
                        st.exception(json_e)
                        categorized_data = None

                    if categorized_data:
                        try:
                            df_updated = pd.DataFrame(categorized_data)
                        except Exception as df_e:
                            st.error(f"Failed to create DataFrame from categorized_data: {df_e}")
                            st.exception(df_e)
                            df_updated = None

                        if df_updated is not None:
                            date_column_name = "transactionDate"
                            if date_column_name in df_updated.columns:
                                try:
                                    df_updated[date_column_name] = df_updated[date_column_name].astype(str) 
                                    df_updated[date_column_name] = pd.to_datetime(df_updated[date_column_name], errors='coerce')
                                    if pd.api.types.is_datetime64_any_dtype(df_updated[date_column_name]):
                                         df_updated[date_column_name] = df_updated[date_column_name].dt.strftime('%d/%m/%Y').fillna('')
                                except Exception as date_fmt_e:
                                    st.error(f"Error formatting date column '{date_column_name}': {date_fmt_e}")
                                    st.exception(date_fmt_e)
                            
                            st.session_state.df_categorized_display = df_updated # Assign to new session state for categorized table
                            # st.rerun() is removed/commented by user
                else:
                    st.error(f"Failed to categorize transactions: {categorize_response.status_code} - {categorize_response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to backend for categorization: {e}")
                st.exception(e)
            except Exception as e:
                st.error(f"An unexpected error occurred during categorization: {e}")
                st.exception(e)

elif uploaded_file and not st.session_state.transformed_data_for_table and st.session_state.llm_header_mapping:
    # This case handles when upload was successful but resulted in no data to transform/display
    # The specific info/error messages would have been shown during the upload process.
    # We ensure the "Categorize Transactions" button doesn't show if there's nothing to categorize.
    # An st.info message might have already been displayed during the upload process.
    pass

# Display the categorized data table if it exists
if 'df_categorized_display' in st.session_state and not st.session_state.df_categorized_display.empty:
    st.subheader("Categorized Data Table:")
    st.dataframe(st.session_state.df_categorized_display)
