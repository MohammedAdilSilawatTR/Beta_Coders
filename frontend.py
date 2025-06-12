import streamlit as st
import requests

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
            # Send both files and data
            response = requests.post("http://localhost:8000/uploadfile/", files=files, data=data)
            if response.status_code == 200:
                st.success("File and business description successfully sent to backend!")
                # st.json(response.json()) # Optionally display response
            else:
                st.error(f"Failed to send data: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to backend: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
