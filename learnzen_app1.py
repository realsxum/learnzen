import streamlit as st
import google.generativeai as genai
import sqlite3
from PyPDF2 import PdfReader
from datetime import date

# 1. SETUP & CONFIGURATION
# Replace with your actual Gemini API Key from Google AI Studio
import os

API_KEY = os.getenv("yourgeminiapikey")

# Database Setup
db_conn = sqlite3.connect("learnzen.db", check_same_thread=False)
db_cursor = db_conn.cursor()
db_cursor.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, task_name TEXT, status TEXT)")
db_conn.commit()

# 2. HELPER FUNCTIONS
def extract_text_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

@st.cache_data(show_spinner=False)
def generate_plan_ai(syllabus_text, exam_date, daily_hours):
    # Expanded list of candidates to handle different environment/SDK versions
    model_candidates = [
        'gemini-2.5-flash',
        'gemini-2.0-flash'
    ]
    
    prompt = f"""
    You are an expert Study Planner.
    Syllabus Content: {syllabus_text[:2000]} 
    Exam Date: {exam_date}
    Available Study Time: {daily_hours} hours per day.

    Create a detailed daily study plan. 
    IMPORTANT: Every specific study task MUST start with the prefix 'TASK:' on a new line.
    Example: TASK: Study Kinematics and solve 10 problems.
    """

    last_error = "Unknown Error"
    for model_name in model_candidates:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            continue # Try next model
            
    return f"ERROR: All models failed. Last error: {last_error}"

# 3. STREAMLIT UI
st.set_page_config(page_title="LearnZen AI", page_icon="📚")

# Custom Title and Subtitle with Minimal Aligned Look
st.markdown('<h1 class="main-heading">LEARNZEN</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-heading">AI Study Planner</p>', unsafe_allow_html=True)
st.markdown("---")

# CSS for UI Fine-tuning
st.markdown("""
    <style>
    /* Background Setup */
    .stApp {
        background: url("https://i.ibb.co/sdJ5qvPy/Gemini-Generated-Image-8p8dmm8p8dmm8p8d.png") no-repeat center center fixed;
        background-size: cover;
    }
    .stApp::before {
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(14, 17, 23, 0.4); z-index: -1;
    }

    /* Header Styling */
    .main-heading {
        color: #BF94FF !important;
        font-size: 5rem !important;
        font-weight: 900 !important;
        text-align: center !important;
        margin-bottom: 0px !important;
        letter-spacing: 5px !important;
        -webkit-text-stroke: 2px #D1B3FF !important;
        text-shadow: 0 0 25px rgba(191, 148, 255, 0.6) !important;
    }
    .sub-heading {
        color: #FFFFFF !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important; /* Thicker as requested */
        text-align: center !important;
        margin-top: -15px !important;
        letter-spacing: 5px !important;
        text-transform: uppercase !important;
        opacity: 0.9 !important;
    }

    /* Glassmorphism for Windows/Containers */
    .stForm, div[data-testid='stExpander'], .stMarkdownContainer, .stTextArea textarea, [data-testid="stFileUploader"] section {
        background: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37) !important;
    }

    /* Glassmorphism for Buttons */
    button[kind="primary"], button[kind="secondary"], .stButton>button {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(5px) !important;
        -webkit-backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(191, 148, 255, 0.4) !important;
    }

    /* Slider Customization */
    div[data-baseweb="slider"] > div > div {
        background: #00FFFF !important; /* Inactive track (right side) - Cyan */
    }
    div[data-baseweb="slider"] > div > div > div > div {
        background: #D1B3FF !important; /* Active track (left side) - Light Violet */
    }
    div[role="slider"] {
        background-color: #FFFFFF !important; /* Thumb - Pure White */
        border: 2px solid #D1B3FF !important;
        box-shadow: 0 0 10px rgba(191, 148, 255, 0.8) !important;
    }
    div[data-testid="stSliderThumbValue"] {
        color: #00FFFF !important;
        font-weight: bold !important;
    }

    /* Vertical alignment for file uploader: Text on top, Button on bottom */
    [data-testid="stFileUploader"] section {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 25px !important;
    }
    [data-testid="stFileUploader"] section > div {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 15px !important;
        width: 100% !important;
    }
    [data-testid="stFileUploader"] div[data-testid="stMarkdownContainer"] {
        text-align: center !important;
        order: 1 !important;
    }
    [data-testid="stFileUploader"] button {
        order: 2 !important;
        margin: 0 !important;
    }
    [data-testid="stFileUploader"] small {
        display: block !important;
        text-align: center !important;
        margin-top: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Main Input Form
with st.form("study_planner_form"):
    # Plan Configuration
    col1, col2 = st.columns([1, 1])
    with col1:
        exam_date = st.date_input("🗓️ When is your exam?", value=None, min_value=date.today())
    with col2:
        daily_hours = st.slider("⏱️ Daily Study Hours", 1, 24, 4)

    # Input Area - Syllabus
    col_pdf, col_text = st.columns([1, 1])
    with col_pdf:
        uploaded_file = st.file_uploader("📂 Upload your Syllabus (PDF)", type="pdf")
    with col_text:
        pasted_text = st.text_area("📝 Or paste your syllabus text here:", height=180) 

    # Action Buttons
    col_gen, col_reset = st.columns([1, 1])
    with col_gen:
        generate_clicked = st.form_submit_button("  Generate My Plan", use_container_width=True)
    with col_reset:
        reset_clicked = st.form_submit_button("  Reset All Tasks", use_container_width=True)

# Processing the Form
if generate_clicked:
    raw_syllabus = ""
    if uploaded_file:
        raw_syllabus = extract_text_from_pdf(uploaded_file)
        st.markdown("### 📄 Your uploaded files:")
        st.info(f"✅ {uploaded_file.name}")
    else:
        raw_syllabus = pasted_text

    if not raw_syllabus:
        st.warning("Please upload a PDF or paste text first.")
    elif exam_date is None:
        st.warning("Please select your exam date first.")
    else:
        with st.spinner("Analyzing syllabus and creating your plan..."):
            full_output = generate_plan_ai(raw_syllabus, exam_date, daily_hours)
            
            if "ERROR" in full_output:
                st.error(full_output)
            else:
                st.session_state['full_plan'] = full_output
                
                # Update Database
                db_cursor.execute("DELETE FROM tasks")
                lines = full_output.split('\n')
                for line in lines:
                    if "TASK:" in line:
                        task_text = line.split("TASK:")[1].strip()
                        db_cursor.execute("INSERT INTO tasks (task_name, status) VALUES (?, 'Pending')", (task_text,))
                db_conn.commit()
                st.success("Plan Generated!")

if reset_clicked:
    db_cursor.execute("DELETE FROM tasks")
    db_conn.commit()
    st.rerun()

# Display Tasks
st.subheader("🗓️ Your Study Tasks")
db_cursor.execute("SELECT id, task_name, status FROM tasks")
current_tasks = db_cursor.fetchall()

if not current_tasks:
    st.info("No tasks yet. Generate a plan above!")
else:
    for task_id, name, status in current_tasks:
        col1, col2 = st.columns([0.8, 0.2])
        
        # Display name with strikethrough if done
        display_name = f"~~{name}~~" if status == 'Done' else name
        col1.markdown(display_name)
        
        # Checkbox for status
        is_done = (status == 'Done')
        if col2.checkbox("Done", value=is_done, key=f"chk_{task_id}"):
            if not is_done:
                db_cursor.execute("UPDATE tasks SET status = 'Done' WHERE id = ?", (task_id,))
                db_conn.commit()
                st.rerun()
        else:
            if is_done:
                db_cursor.execute("UPDATE tasks SET status = 'Pending' WHERE id = ?", (task_id,))
                db_conn.commit()
                st.rerun()

