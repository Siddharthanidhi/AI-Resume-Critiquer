import streamlit as st # type: ignore
import PyPDF2 # type: ignore
import io
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.pdfgen import canvas # type: ignore
import tempfile

# Load API key from .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Streamlit page setup
st.set_page_config(page_title="AI Resume Critiquer", page_icon="📄", layout="centered")
st.title("📄 AI Resume Critiquer")
st.markdown("Upload your resume and get AI-powered feedback tailored to your target role.")

# File upload and input
uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role you're targeting (optional)")
analyze = st.button("🔍 Analyze Resume")

# PDF extractor
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

# File type handler
def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    return uploaded_file.read().decode("utf-8")

# PDF writer from text
def create_pdf_from_text(text, filename="analysis.pdf"):
    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    c = canvas.Canvas(temp_path, pagesize=letter)
    width, height = letter

    lines = text.split("\n")
    y = height - 50
    for line in lines:
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(40, y, line.strip())
        y -= 15

    c.save()
    return temp_path

# Main logic
if analyze and uploaded_file:
    try:
        file_content = extract_text_from_file(uploaded_file)

        if not file_content.strip():
            st.error("❌ The file appears to be empty.")
            st.stop()

        # Prompt with scoring
        prompt = f"""
Please analyze this resume and provide constructive feedback.
Rate the following sections from 1 to 10:

1. Content clarity and impact
2. Skills presentation
3. Experience descriptions
4. Relevance to the role of {job_role if job_role else 'a general job'}

Then, provide an overall score and specific suggestions for improvement.

Resume content:
{file_content}

Respond in clear sections with titles and scores, e.g., "Skills: 7/10" followed by explanation.
"""

        # Gemini model
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7,
            max_output_tokens=1500
        )

        response = llm.invoke([
            SystemMessage(content="You are an expert resume reviewer with years of experience in HR and recruitment."),
            HumanMessage(content=prompt)
        ])

        feedback_text = response.content
        st.markdown("### ✅ Resume Analysis")
        st.markdown(feedback_text)

        # PDF download button
        pdf_path = create_pdf_from_text(feedback_text)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="📥 Download Feedback as PDF",
                data=pdf_file,
                file_name="resume_analysis.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
