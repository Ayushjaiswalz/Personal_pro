import streamlit as st
import requests

BACKEND_URL = "https://personal-pro-atg8.onrender.com/upload"

st.title("📤 File Upload System")

uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
custom_name = st.text_input("Enter a custom filename (without extension)")

if st.button("Upload", disabled=not (uploaded_file and custom_name)):
    if uploaded_file and custom_name:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {"custom_name": custom_name}  # Send filename separately

        response = requests.post(BACKEND_URL, files=files, data=data)

        if response.status_code == 200:
            st.success(f"✅ File uploaded successfully!\n🔗 [View on Google Drive]({response.json()['drive_url']})")
        else:
            st.error("❌ Upload failed. Try again.")
