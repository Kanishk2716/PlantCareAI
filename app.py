import streamlit as st
from PIL import Image
import os
from dotenv import load_dotenv
import google.generativeai as genai
import time
from datetime import datetime
import io
from fpdf import FPDF

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.0-flash-exp")


# App Layout
st.set_page_config(page_title="PlantCare AI", layout="wide")



# Custom CSS with nature-inspired theme
st.markdown("""
    <style>
    /* Plant-Inspired Theme */
    .stApp {
        background-color: #f0f7e9;
        color: #2c5e1a;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, #4a7c59 0%, #7cb342 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Section Headers */
    .section-header {
        color: #2e7d32;
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #7cb342;
        padding-bottom: 0.5rem;
    }
    
    

    
    /* Buttons */
    .stButton > button {
        background-color: #7cb342;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #4a7c59;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #e8f5e9;
        border-right: 1px solid #7cb342;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-color: #7cb342;
    }

    /* File Uploader */
    .stFileUploader {
        background-color: #ffffff;
        border: 2px dashed #7cb342;
        border-radius: 15px;
        padding: 1rem;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #e8f5e9;
        border-radius: 10px;
    }

    /* Select Box */
    .stSelectbox {
        background-color: #ffffff;
        border-radius: 10px;
    }

    /* Text Input */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        border-radius: 10px;
    }

    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'archive' not in st.session_state:
    st.session_state.archive = []


# PDF Generation Function
def create_pdf_report(image, analysis):
    try:
        # Replace problematic characters
        analysis = analysis.replace("’", "'")
        
        # Initialize PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set up the title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'PlantCare AI Analysis Report', ln=True, align='C')
        
        # Add timestamp
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True, align='R')
        
        # Convert image to RGB mode if it's not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save to temporary file
        temp_img_path = "temp_image.png"
        image.save(temp_img_path, 'PNG', optimize=True)
        
        # Add image to PDF
        pdf.image(temp_img_path, x=10, w=190)
        os.remove(temp_img_path)  # Clean up temp file
        
        # Add spacing and analysis content
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Analysis Results', ln=True)
        pdf.set_font('Arial', '', 11)
        
        # Add analysis text
        paragraphs = analysis.split('\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                if paragraph.strip().isupper() or paragraph.startswith('#'):
                    pdf.set_font('Arial', 'B', 12)
                    pdf.ln(5)
                    pdf.cell(0, 10, paragraph.strip(), ln=True)
                    pdf.set_font('Arial', '', 11)
                else:
                    pdf.multi_cell(0, 6, paragraph.strip())
                    pdf.ln(2)
        
        # Return PDF content as bytes
        return pdf.output(dest='S').encode('latin-1', errors='replace')
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None



def get_disease_analysis(image_parts):
    base_prompt = """
    Analyze this plant/leaf image and provide a detailed report with the following sections.
    """
    
    if "Beginner" in experience_level:
        base_prompt += """
        Please use simple, non-technical language and focus on practical advice. 
        Explain terms clearly and provide basic, step-by-step instructions.
        """
    elif "Hobbyist" in experience_level:
        base_prompt += """
        Use a mix of common and technical terms, with brief explanations for specialized concepts.
        Provide moderate detail in care instructions.
        """
    else:  # Experienced
        base_prompt += """
        You may use technical terminology and provide detailed scientific information.
        Include advanced care techniques and comprehensive treatment options.
        """
    
    analysis_prompt = base_prompt + """
    Please provide:
    
    1. Quick Summary
    - Simple description of what you see
    - Whether this needs immediate attention
    - How serious the situation appears
    
    2. Plant Condition
    - Visible symptoms
    - Affected parts
    - Signs of spreading
    
    3. Likely Causes
    - Common reasons this happens
    - Environmental factors
    - Care-related factors
    
    4. Recommended Actions
    - Immediate steps to take
        -Isolate the affected plant if spreading symptoms are visible.
        -Remove visibly damaged leaves to prevent further infection.
        -Adjust watering habits if over/underwatering is suspected.
    - Basic care adjustments
    - When to consult an expert
    
    5. Care Instructions
    - Step-by-step treatment guide
    - Daily/weekly care routine
    - Things to avoid
    
    6. Prevention Guide
    - Early warning signs
    - Preventive measures
    - Best practices for plant health
    
    7. Additional Tips
    - Common mistakes to avoid
    - Signs of improvement to look for
    - Related issues to watch for

    8.Optional Ecosystem Impact (for experienced users)
    -Potential effects on nearby plants
    -Impact on soil health
    -Suggestions to mitigate broader environmental issues
    """
    
    try:
        response = model.generate_content([analysis_prompt, image_parts[0]])
        return response.text
    except Exception as e:
        st.error(f"Analysis Error: {str(e)}")
        return None
    
def input_image_setup(uploaded_file):
    try:
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            image_parts = [{"mime_type": uploaded_file.type, "data": bytes_data}]
            return image_parts
        else:
            raise FileNotFoundError("No plant image submitted")
    except Exception as e:
        st.error(f"Image Processing Error: {str(e)}")
        return None
    
def save_to_archive(image_name, analysis):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "image_name": image_name,
        "analysis": analysis
    }
    st.session_state.archive.append(entry)

# Main Header
st.markdown("""
    <div class="header-container">
        <h1>🌿 PlantCare AI</h1>
        <p style="font-size: 1.2rem; opacity: 0.9;">Your Digital Botanist for Plant Health & Care</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🍃 Analysis Options")
    
    analysis_focus = st.multiselect(
        "What would you like to know?",
        options=[
            "Basic Disease Information",
            "Care Instructions",
            "Prevention Tips",
            "Organic Treatment Options",
            "When to Seek Expert Help",
            "Similar Disease Patterns"
        ],
        default=["Basic Disease Information", "Care Instructions"],
        help="Select the types of information you need about your plant"
    )
    
    experience_level = st.radio(
        "I am a...",
        options=[
            " Beginner - New to plant care",
            " Hobbyist - Some experience with plants",
            " Experienced - Regular gardening experience"
        ],
        help="This helps us adjust the language and detail level of our analysis"
    )
    
    show_archive = st.checkbox(
        "📚 View Previous Analyses",
        help="See your previous plant analysis reports"
    )
    
    st.markdown("---")
    st.markdown("### 🌱 About PlantCare AI")
    st.markdown("""
        A beginner-friendly platform for identifying plant problems and getting care advice. 
        Simply upload a photo of your plant, and we'll help you understand:
        - What might be affecting your plant
        - How to care for it
        - When to take preventive measures
        - Simple treatment options
    """)
    
    st.markdown("---")
    st.markdown("### 📸 Tips for Better Results")
    st.markdown("""
        Photo Tips:
        - Take photos in natural lighting
        - Include both healthy and affected areas
        - Take close-up shots of specific problems
        - Include multiple angles if possible
    """)

# Main Content
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="section-header">📷 Image Upload</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload plant/leaf image for analysis", type=["jpg", "jpeg", "png", "tiff"])
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-header">👁️ Preview</div>', unsafe_allow_html=True)
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Plant Image", use_container_width=True)

# Analysis Generation
if uploaded_file:
    st.markdown("---")
    st.markdown('<div class="section-header">🔬 Plant Health Analysis</div>', unsafe_allow_html=True)
    
    if st.button("Analyze Plant Condition", type="primary"):
        with st.spinner('Analyzing plant condition...'):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            image_data = input_image_setup(uploaded_file)
            if image_data:
                analysis = get_disease_analysis(image_data)
                if analysis:
                    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
                    st.markdown("### 📊 Analysis Results")
                    st.markdown(analysis)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    save_to_archive(uploaded_file.name, analysis)
                    
                    # Create download buttons container
                    download_col1, download_col2 = st.columns(2)
                    
                    # Text download option
                    with download_col1:
                        st.download_button(
                            label="📄 Download Text Report",
                            data=analysis,
                            file_name=f"plant_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    
                    # PDF download option
                    with download_col2:
                        pdf_content = create_pdf_report(Image.open(uploaded_file), analysis)
                        if pdf_content is not None:
                            st.download_button(
                                label="📑 Download PDF Report",
                                data=pdf_content,
                                file_name=f"plant_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            )

# Archive Display
if show_archive and st.session_state.archive:
    st.markdown("---")
    st.markdown('<div class="section-header">📚 Analysis Archive</div>', unsafe_allow_html=True)
    
    for i, entry in enumerate(reversed(st.session_state.archive)):
        with st.expander(f"Analysis {i+1}: {entry['image_name']} - {entry['timestamp']}"):
            st.markdown("**Analysis Results:**")
            st.markdown(entry['analysis'])

    
