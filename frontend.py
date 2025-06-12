import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("Excel File Uploader and Viewer")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:

    # Display the Excel file content
    try:
        # Make sure to use the uploaded_file object directly with read_excel
        df = pd.read_excel(uploaded_file)
        st.subheader("Excel File Content:")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error reading or displaying Excel file: {e}")

    if st.button("Upload File"):
        # To send the file, we need to reset the file pointer after reading it with pandas
        uploaded_file.seek(0)
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        try:
            response = requests.post("http://localhost:8000/uploadfile/", files=files)
            if response.status_code == 200:
                st.success("File successfully sent to backend!")
            else:
                st.error(f"Failed to send file: {response.text}")
        except Exception as e:
            st.error(f"Error sending file: {e}")
