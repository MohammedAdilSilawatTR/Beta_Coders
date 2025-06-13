import streamlit as st
import requests
import pandas as pd # Import pandas for DataFrame
import json # Added import
import time # Added import for time tracking

st.set_page_config(page_title="Smart AI Mapping", page_icon="🤖", layout="wide")

st.title("AI Mapping and Categorization Tool 🤖")

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
if 'df_category_summary' not in st.session_state: # New session state for category summary table
    st.session_state.df_category_summary = pd.DataFrame()
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
        # Reset categorized display and summary when new file is uploaded or remapped
        st.session_state.df_categorized_display = pd.DataFrame()
        st.session_state.df_category_summary = pd.DataFrame()
        st.session_state.df_display = pd.DataFrame() # Also reset mapped data table
        st.session_state.transformed_data_for_table = []
        
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        data = {"business_description": st.session_state.business_description}

        try:
            start_time_mapping = time.time()
            with st.spinner("Processing file and mapping headers..."):
                response = requests.post("http://localhost:8000/uploadfile/", files=files, data=data)
            end_time_mapping = time.time()
            mapping_duration = end_time_mapping - start_time_mapping
            
            if response.status_code == 200:
                st.info(f"Header mapping completed in {mapping_duration:.2f} seconds.")
                st.success("File processed successfully!")
                
                response_data = response.json()
                st.session_state.original_excel_headers = response_data.get("headers", []) 
                st.session_state.data_rows = response_data.get("non_empty_rows", []) 
                st.session_state.llm_header_mapping = response_data.get("header_mapping", {})

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
                        st.session_state.df_display = df
                    else:
                        st.info("Could not transform data for table display.")
                        st.session_state.df_display = pd.DataFrame()
            else:
                st.error(f"Failed to process file: {response.status_code} - {response.text}")
                st.session_state.transformed_data_for_table = []
                st.session_state.df_display = pd.DataFrame()
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to backend: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

# Display LLM Header Mapping if it exists
if 'llm_header_mapping' in st.session_state and st.session_state.llm_header_mapping:
    st.subheader("LLM Header Mapping:")
    mapping_list_for_df = [{"Predefined Column": key, "Mapped Excel Header": value} 
                           for key, value in st.session_state.llm_header_mapping.items()]
    df_mapping = pd.DataFrame(mapping_list_for_df)
    st.dataframe(df_mapping, width=500)

# Display Column Mapped Data Table if it exists
if 'df_display' in st.session_state and not st.session_state.df_display.empty:
    st.subheader("Column Mapped Data Table:")
    st.dataframe(st.session_state.df_display)

    # Add "Categorize Transactions" button only if there's mapped data
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
                start_time_categorization = time.time()
                with st.spinner("Categorizing transactions..."):
                    categorize_response = requests.post("http://localhost:8000/categorize-transactions/", json=payload)
                end_time_categorization = time.time()
                categorization_duration = end_time_categorization - start_time_categorization
                
                if categorize_response.status_code == 200:
                    st.info(f"Transaction categorization completed in {categorization_duration:.2f} seconds.")
                    st.success("Transactions categorized successfully!")
                    categorized_data = categorize_response.json()
                    if categorized_data:
                        df_updated = pd.DataFrame(categorized_data)
                        date_column_name = "transactionDate"
                        if date_column_name in df_updated.columns:
                            try:
                                df_updated[date_column_name] = pd.to_datetime(df_updated[date_column_name], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
                            except Exception as date_fmt_e:
                                st.error(f"Error formatting date column '{date_column_name}': {date_fmt_e}")
                        st.session_state.df_categorized_display = df_updated
                    else:
                        st.session_state.df_categorized_display = pd.DataFrame() 
                else:
                    st.error(f"Failed to categorize transactions: {categorize_response.status_code} - {categorize_response.text}")
                    st.session_state.df_categorized_display = pd.DataFrame()
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to backend for categorization: {e}")
                st.session_state.df_categorized_display = pd.DataFrame()
            except Exception as e:
                st.error(f"An unexpected error occurred during categorization: {e}")
                st.session_state.df_categorized_display = pd.DataFrame()

# Display the categorized data table (editable) if it exists and process edits
if 'df_categorized_display' in st.session_state and \
   isinstance(st.session_state.df_categorized_display, pd.DataFrame) and \
   not st.session_state.df_categorized_display.empty:
    
    st.subheader("Categorized Data Table (Editable Categories):")
    
    ALL_POSSIBLE_CATEGORIES = sorted(list(set([
        "General Administration Expenses", "Turnover", "Premises Costs", 
        "Legal and Professional Costs", "Advertising and Promotion Costs", 
        "Other Business Expenses", "Travel and Subsistence", "Subcontractor Expense", 
        "Other Direct Costs", "Motor Expenses", "Business Entertainment Costs", 
        "Employee Costs", "Depreciation", "Bad Debts", "Interest", "Other Income", 
        "Cost of Goods", "Personal", "Repairs",
        "Uncategorized", "Missing or Invalid Description", "Error in Categorization"
    ])))

    column_configuration = {
        "category": st.column_config.SelectboxColumn(
            "Category",
            help="Select the correct category for the transaction",
            options=ALL_POSSIBLE_CATEGORIES,
            required=True 
        )
    }
    # Make other columns non-editable
    for col_name in st.session_state.df_categorized_display.columns:
        if col_name.lower() != 'category':
            column_configuration[col_name] = st.column_config.TextColumn(col_name, disabled=True)

    edited_df = st.data_editor(
        st.session_state.df_categorized_display, # Input for the editor for this run
        column_config=column_configuration,
        num_rows="fixed",
        key="category_editor_table_final_v2", # Unique key
        use_container_width=True
    )

    # Update session state for the *next* rerun with the data from the editor.
    # And use edited_df for calculations in *this* rerun.
    st.session_state.df_categorized_display = edited_df

    # Calculate summary based on the DIRECT output of data_editor (edited_df)
    try:
        if edited_df is not None and isinstance(edited_df, pd.DataFrame):
            current_df_for_summary = edited_df.copy() 
            if 'amount' in current_df_for_summary.columns and 'category' in current_df_for_summary.columns:
                current_df_for_summary['amount'] = pd.to_numeric(current_df_for_summary['amount'], errors='coerce').fillna(0)
                category_summary_df = current_df_for_summary.groupby('category')['amount'].sum().reset_index()
                category_summary_df.columns = ['Category', 'Total Amount']
                st.session_state.df_category_summary = category_summary_df
            elif 'category' not in current_df_for_summary.columns:
                st.warning("The 'category' column is missing in edited data, cannot calculate category summary.")
                st.session_state.df_category_summary = pd.DataFrame() 
            else: 
                st.warning("The 'amount' column is missing in edited data, cannot calculate category summary.")
                st.session_state.df_category_summary = pd.DataFrame()
        else:
            st.warning("Data editor did not return valid data for summary.")
            st.session_state.df_category_summary = pd.DataFrame()
    except Exception as e:
        st.error(f"Error calculating category summary: {e}")
        st.session_state.df_category_summary = pd.DataFrame()

# Display the category summary table if it exists
if 'df_category_summary' in st.session_state and not st.session_state.df_category_summary.empty:
    st.subheader("Category Summary:")
    st.dataframe(st.session_state.df_category_summary, width=500)
