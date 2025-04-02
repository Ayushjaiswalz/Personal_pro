# import streamlit as st
# import requests

# BACKEND_URL = "https://personal-pro-atg8.onrender.com/upload"

# st.title("📤 File Upload System")

# uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
# custom_name = st.text_input("Enter a custom filename (without extension)")

# if st.button("Upload", disabled=not (uploaded_file and custom_name)):
#     if uploaded_file and custom_name:
#         files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
#         data = {"custom_name": custom_name}  # Send filename separately

#         response = requests.post(BACKEND_URL, files=files, data=data)

#         if response.status_code == 200:
#             st.success(f"✅ File uploaded successfully!\n🔗 [View on Google Drive]({response.json()['drive_url']})")
#         else:
#             st.error("❌ Upload failed. Try again.")



import gradio as gr
import requests

BACKEND_URL = "https://personal-pro-atg8.onrender.com/upload"

def upload_file(file, custom_name):
    if file is None or not custom_name:
        return "❌ Please provide a file and a custom filename.", None

    # Read file content
    files = {"file": (file.name, file.read())}  # Removed 'file.type'
    data = {"custom_name": custom_name}

    response = requests.post(BACKEND_URL, files=files, data=data)

    if response.status_code == 200:
        drive_url = response.json()["drive_url"]
        return f"✅ File uploaded successfully! [View on Google Drive]({drive_url})", drive_url
    else:
        return "❌ Upload failed. Try again.", None

iface = gr.Interface(
    fn=upload_file,
    inputs=[
        gr.File(label="Upload Image"), 
        gr.Textbox(label="Custom Filename (without extension)")
    ],
    outputs=[
        gr.Markdown(), 
        gr.Textbox(label="Google Drive URL")
    ],
    title="📤 File Upload System",
    description="Upload an image and get the Google Drive link."
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=10000)
