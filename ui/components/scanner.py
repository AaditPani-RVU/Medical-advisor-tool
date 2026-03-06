"""
Prescription Scanner UI Component.
"""

import streamlit as st
import httpx
from ui.components.cards import render_content_card

# We need to use httpx directly for handling multipart form file uploads since api_post assumes JSON.
API_BASE = "http://localhost:8000"

def render_scanner_page(api_post):
    """Render the prescription scanner page."""
    
    st.title("📄 Prescription Scanner")
    
    st.markdown(
        """<div class="disclaimer-box">⚠️ <b>Educational content only.</b> 
        This tool uses OCR AI to read your prescription and suggest relevant educational videos.
        It is NOT providing medical advice or diagnosing you.</div>""",
        unsafe_allow_html=True,
    )
    
    st.info("Upload a clear photo of a medical prescription. We'll extract the text and find helpful verified videos about the medications or conditions.")

    # File uploader allowing camera capture or file selection
    uploaded_file = st.file_uploader("Upload or take a picture of a Prescription", type=["jpg", "jpeg", "png", "webp"])
    
    # Or explicitly use camera
    camera_file = st.camera_input("Take a picture")
    
    file_to_process = uploaded_file or camera_file

    if file_to_process is not None:
        st.image(file_to_process, caption="Uploaded Image", use_column_width=True)
        
        if st.button("Scan Prescription", type="primary"):
            with st.spinner("Scanning document using AI Vision..."):
                try:
                    # Reset pointer to start of file
                    file_to_process.seek(0)
                    
                    # Prepare file for upload
                    files = {"file": (file_to_process.name, file_to_process, file_to_process.type)}
                    
                    response = httpx.post(f"{API_BASE}/analyze-prescription", files=files, timeout=45.0)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if "error" in data:
                         st.error(data["error"])
                    else:
                         ocr_method = data.get("ocr_method", "AI Vision")
                         st.success(f"Scan complete using {ocr_method}!")
                         
                         entities = data.get("extracted_entities", {})
                         diagnoses = entities.get("diagnoses", [])
                         medications = entities.get("medications", [])
                         
                         col1, col2 = st.columns(2)
                         with col1:
                             st.markdown("### 🩺 Diagnoses / Conditions")
                             if diagnoses:
                                 for d in diagnoses:
                                     st.markdown(f"- {d}")
                             else:
                                 st.caption("None clearly found.")
                                 
                         with col2:
                             st.markdown("### 💊 Medications")
                             if medications:
                                 for m in medications:
                                     st.markdown(f"- {m}")
                             else:
                                 st.caption("None clearly found.")
                                 
                         with st.expander("Show raw extracted text"):
                             st.text(data.get("extracted_text_preview", ""))
                             
                         # Show recommendations
                         recommendations = data.get("recommendations", [])
                         st.markdown("---")
                         st.markdown("### 📺 Recommended Verified Videos")
                         
                         if recommendations:
                             for item in recommendations:
                                 render_content_card(item)
                         else:
                             st.info("We couldn't find any specific videos matching your prescription in our database. Try checking the Verified Feed.")
                             
                except Exception as e:
                     st.error(f"Failed to analyze image: {e}")
