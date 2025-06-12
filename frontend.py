import streamlit as st
import requests
import pandas as pd # Import pandas for DataFrame

st.set_page_config(page_title="Smart AI Mapping", page_icon="🤖", layout="wide")

st.title("Excel File Uploader")

# Add a text input for business description
business_description = st.text_input("Enter Business Description (optional)")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    if st.button("Upload File"):
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        # Prepare data payload for form fields
        data = {"business_description": business_description}

        try:
            with st.spinner("Processing file and mapping headers..."):
                response = requests.post("http://localhost:8000/uploadfile/", files=files, data=data)
            
            if response.status_code == 200:
                st.success("File processed successfully!")
                
                response_data = response.json()
                original_excel_headers = response_data.get("headers", []) 
                data_rows = response_data.get("non_empty_rows", []) 
                llm_header_mapping = response_data.get("header_mapping", {})

                st.subheader("LLM Header Mapping Received:")
                st.json(llm_header_mapping)

                if not data_rows:
                    st.info("No data rows received from backend to display.")
                elif not original_excel_headers:
                    st.info("No original headers received from backend.")
                elif not llm_header_mapping or not any(llm_header_mapping.values()): # Check if mapping is empty or all values are None
                    st.info("No valid header mapping received from LLM, or LLM could not map any headers.")
                else:
                    original_header_to_index = {header: i for i, header in enumerate(original_excel_headers)}
                    
                    # These are the columns we want in our final table, derived from LLM mapping keys
                    # These keys are expected to be the predefined column names.
                    final_table_columns = list(llm_header_mapping.keys())

                    transformed_data_for_table = []
                    for row_values in data_rows:
                        new_mapped_row = {}
                        for predefined_col_name in final_table_columns:
                            original_excel_header_for_this_predefined_col = llm_header_mapping.get(predefined_col_name)

                            if original_excel_header_for_this_predefined_col and \
                               original_excel_header_for_this_predefined_col in original_header_to_index:
                                
                                idx_in_original_row = original_header_to_index[original_excel_header_for_this_predefined_col]
                                
                                if idx_in_original_row < len(row_values):
                                    new_mapped_row[predefined_col_name] = row_values[idx_in_original_row]
                                else:
                                    new_mapped_row[predefined_col_name] = None 
                            else:
                                new_mapped_row[predefined_col_name] = None 
                        transformed_data_for_table.append(new_mapped_row)

                    if transformed_data_for_table:
                        st.subheader("Mapped Data Table:")
                        df = pd.DataFrame(transformed_data_for_table)
                        
                        # Convert known date columns from string back to datetime for better display
                        # Assuming "transactionDate" is one of the predefined column names that might contain dates
                        date_column_name = "transactionDate" # This should match a key in PREDEFINED_COLUMNS
                        if date_column_name in df.columns:
                            # Convert to datetime objects first
                            df[date_column_name] = pd.to_datetime(df[date_column_name], errors='coerce')
                            # Then format the datetime objects to "dd/MM/yyyy" string format
                            # NaT values will remain NaT, which will likely be displayed as blank or 'NaT' by Streamlit
                            if pd.api.types.is_datetime64_any_dtype(df[date_column_name]):
                                df[date_column_name] = df[date_column_name].dt.strftime('%d/%m/%Y').fillna('') # fillna for NaT if needed

                        # Ensure columns are displayed in the order derived from LLM mapping keys
                        display_df_cols = [col for col in final_table_columns if col in df.columns]
                        if display_df_cols: # Only display if there are columns to show
                            st.dataframe(df[display_df_cols])
                        else:
                            st.info("No columns to display in the table after processing.")
                    else:
                        st.info("Could not transform data for table display (e.g., mapping issues led to empty data).")
            else:
                st.error(f"Failed to process file: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to backend: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
