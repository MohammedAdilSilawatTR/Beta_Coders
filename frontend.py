import streamlit as st
import requests

st.title("Excel File Uploader")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    if st.button("Upload File"):
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        try:
            response = requests.post("http://localhost:8000/uploadfile/", files=files)
            if response.status_code == 200:
                st.success("File successfully sent to backend!")
            else:
                st.error(f"Failed to send file: {response.text}")
        except Exception as e:
            st.error(f"Error: {e}")