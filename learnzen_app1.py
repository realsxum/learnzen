import streamlit as st
import google.generativeai as genai
import sqlite3
from PyPDF2 import PdfReader
from datetime import date

# 1. SETUP & CONFIGURATION
# Replace with your actual Gemini API Key from Google AI Studio
API_KEY = "AIzaSyCzIqzq9KwdRFu0tkq4xjyla74pxT-Hg60"
genai.configure(api_key=API_KEY)

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

def generate_plan_ai(syllabus_text, exam_date, daily_hours):
    # This list handles naming changes in Python 3.14 / v1beta API
    model_names = [
        'models/gemini-2.0-flash',
        'models/gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-2.5-flash'
    ]
    
    selected_model = None
    # Try to find a working model
    for name in model_names:
        try:
            m = genai.GenerativeModel(name)
            # Short test to see if the model name is valid
            m.generate_content("Hi", generation_config={"max_output_tokens": 1})
            selected_model = m
            break
        except Exception:
            continue

    if not selected_model:
        return "ERROR: Could not find a compatible model. Check your API key or internet connection."

    prompt = f"""
    You are an expert Study Planner.
    Syllabus Content: {syllabus_text[:2000]} 
    Exam Date: {exam_date}
    Available Study Time: {daily_hours} hours per day.

    Create a detailed daily study plan. 
    IMPORTANT: Every specific study task MUST start with the prefix 'TASK:' on a new line.
    Example: TASK: Study Kinematics and solve 10 problems.
    """

    try:
        response = selected_model.generate_content(prompt)
        if response and response.text:
            return response.text
        return "ERROR: AI returned an empty response."
    except Exception as e:
        return f"ERROR: {str(e)}"

# 3. STREAMLIT UI
st.set_page_config(page_title="LearnZen AI", page_icon="📚")
st.title("🫰 LearnZen: AI Study Planner")
st.markdown("---")

# Plan Configuration
col1, col2 = st.columns([1, 1])
with col1:
    exam_date = st.date_input("🗓️ When is your exam?", value=None, min_value=date.today())
with col2:
    daily_hours = st.slider("⏱️ Daily Study Hours", 1, 24, 4)

# CSS for UI Fine-tuning
st.markdown("""
    <style>
    /* Center-align the file uploader elements */
    [data-testid="stFileUploader"] section {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 20px;
    }
    [data-testid="stFileUploader"] section > div {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Main Area - Input
col_pdf, col_text = st.columns([1, 1])
with col_pdf:
    uploaded_file = st.file_uploader("📂 Upload your Syllabus (PDF)", type="pdf")
with col_text:
    pasted_text = st.text_area("📝 Or paste your syllabus text here:", height=180) # Increased height to match uploader

raw_syllabus = ""
if uploaded_file:
    raw_syllabus = extract_text_from_pdf(uploaded_file)
    st.markdown("### 📄 Your uploaded files:")
    st.info(f"✅ {uploaded_file.name}")
else:
    raw_syllabus = pasted_text

# Action Buttons
col_gen, col_reset = st.columns([1, 1])

with col_gen:
    if st.button("🚀 Generate My Plan", use_container_width=True):
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

with col_reset:
    if st.button("🔄 Reset All Tasks", use_container_width=True):
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