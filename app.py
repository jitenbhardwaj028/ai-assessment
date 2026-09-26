import streamlit as st
import pandas as pd
from google import genai

# Page configuration
st.set_page_config(
    page_title="Secure AI Assessment",
    page_icon="🔒",
    layout="centered"
)

# 1. Load the Excel database
@st.cache_data
def load_students():
    try:
        df = pd.read_excel("students.xlsx")
        df["RollNumber"] = df["RollNumber"].astype(str).str.strip()
        return df
    except Exception:
        return None

df_students = load_students()

st.title("🔒 Welcome to Assessment Portal")

if df_students is None:
    st.error("Error: Could not find students.xlsx. Please upload it to your GitHub repository.")
    st.stop()

# 2. Authentication State Management
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.student_roll = ""

# 3. Login Screen
if not st.session_state.authenticated:
    st.markdown("Please enter your roll number to access the assessment.")
    entered_roll = st.text_input("Roll Number:")

    if st.button("Verify & Start Assessment"):
        match = df_students[df_students["RollNumber"] == entered_roll.strip()]

        if not match.empty:
            st.session_state.authenticated = True
            st.session_state.student_roll = entered_roll.strip()
            st.success("Access Granted!")
            st.rerun()
        else:
            st.error("Invalid Roll Number. You are not authorized for this assessment.")

# 4. Assessment Screen (Only visible when logged in)
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**Logged in Roll Number:** {st.session_state.student_roll}")
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.messages = []
            st.rerun()

    st.divider()
    st.subheader("AI Evaluator")

    # Initialize Gemini Client using Streamlit Secret
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception:
        st.error("API Key is missing in Streamlit Secrets! Please configure it in your app settings.")
        st.stop()

    # Chat history initialization (starts automatically with Question 1)
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    f"Welcome, Candidate {st.session_state.student_roll}.\n\n"
                    "This is your 40-question comprehensive assessment on **Strategic Pricing Models**.\n"
                    "The assessment contains **MCQs (Q1–15)**, **True/False Statements (Q16–25)**, and **Scenario Analysis (Q26–40)**.\n\n"
                    "---\n"
                    "**Question 1/40 (MCQ):**\n"
                    "Which pricing strategy involves setting an intentionally high initial price to target price-insensitive early adopters before gradually lowering it to capture broader market segments?\n"
                    "A) Penetration Pricing\n"
                    "B) Price Skimming\n"
                    "C) Cost-Plus Pricing\n"
                    "D) Freemium Pricing\n\n"
                    "*Reply with your choice (A, B, C, or D) or your reasoning.*"
                ),
            }
        ]

    # Render conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input for student answers
    if user_prompt := st.chat_input("Type your answer or option letter here..."):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Assessment system instructions
        assessment_prompt = f"""
You are an academic examiner conducting a 40-question examination on STRATEGIC PRICING MODELS for student roll number {st.session_state.student_roll}.

TOPICS COVERED:
Cost-Plus, Value-Based, Price Skimming, Penetration, Freemium, Dynamic/Surge, Tiered/Feature-based, Bundling, Loss-Leader, Psychological Pricing, and SaaS Pricing Metrics.

QUESTION STRUCTURE (TOTAL 40 QUESTIONS):
- Questions 1 to 15: Multiple Choice Questions (MCQs with 4 options: A, B, C, D).
- Questions 16 to 25: True or False questions (ask for True/False and a 1-sentence rationale).
- Questions 26 to 40: Scenario-based, application, or margin/numerical questions.

WORKFLOW RULES:
1. EVALUATE: For the submitted answer:
   - State clearly if it is Correct, Partially Correct, or Incorrect.
   - Provide a brief 1-2 sentence explanation.
   - Assign a score out of 5 for that question (e.g., Score: 5/5).
2. PROGRESS:
   - Present the next question clearly with the counter (e.g., "**Question [X]/40 ([Type]):**").
   - Maintain the required format according to the question number (MCQ, True/False, or Scenario).
3. CONCLUSION:
   - Once Question 40 has been answered and evaluated, stop asking questions.
   - Provide a final scorecard with Total Marks out of 200, overall percentage, recognized strengths, and core conceptual gaps.
"""

        # Build full conversation history for context continuity
        formatted_contents = []
        for msg in st.session_state.messages:
            formatted_contents.append({
                "role": "model" if msg["role"] == "assistant" else "user",
                "parts": [{"text": msg["content"]}]
            })

        with st.spinner("AI is evaluating your response..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=formatted_contents,
                    config={
                        "system_instruction": assessment_prompt
                    },
                )
                ai_reply = response.text
            except Exception as e:
                ai_reply = f"Error details: {str(e)}"

        with st.chat_message("assistant"):
            st.markdown(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
