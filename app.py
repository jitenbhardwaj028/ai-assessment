from google import genai
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title='Secure AI Assessment', page_icon='🔒', layout='centered'
)

# 1. Load the Excel database
@st.cache_data
def load_students():
  try:
    df = pd.read_excel('students.xlsx')
    df['RollNumber'] = df['RollNumber'].astype(str).str.strip()
    return df
  except Exception as e:
    return None


df_students = load_students()

st.title('🔒 Secure AI Assessment Portal')

if df_students is None:
  st.error(
      'Error: Could not find students.xlsx. Please upload it to your GitHub'
      ' repository.'
  )
  st.stop()

# 2. Authentication State Management
if 'authenticated' not in st.session_state:
  st.session_state.authenticated = False
  st.session_state.student_roll = ''

# 3. Login Screen
if not st.session_state.authenticated:
  st.markdown('Please enter your roll number to access the assessment.')
  entered_roll = st.text_input('Roll Number:')

  if st.button('Verify & Start Assessment'):
    match = df_students[df_students['RollNumber'] == entered_roll.strip()]

    if not match.empty:
      st.session_state.authenticated = True
      st.session_state.student_roll = entered_roll.strip()
      st.success('Access Granted!')
      st.rerun()
    else:
      st.error(
          'Invalid Roll Number. You are not authorized for this assessment.'
      )

# 4. Assessment Screen (Only visible if logged in)
else:
  col1, col2 = st.columns([3, 1])
  with col1:
    st.write(f'**Logged in Roll Number:** {st.session_state.student_roll}')
  with col2:
    if st.button('Logout'):
      st.session_state.authenticated = False
      st.session_state.messages = []
      st.rerun()

  st.divider()
  st.subheader('AI Evaluator')

  # Initialize Gemini Client using the secure secret key
  try:
    client = genai.Client(api_key=st.secrets['GEMINI_API_KEY'])
  except Exception:
    st.error('API Key is missing in Streamlit Secrets! Please configure it.')
    st.stop()

  # Chat history state
 # -------------------------------------------------------------
    # 4. CHAT HISTORY INITIALIZATION (STARTS WITH QUESTION 1)
    # -------------------------------------------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    f"Welcome, Candidate {st.session_state.student_roll}.\n\n"
                    "This is your 40-question comprehensive assessment on **Strategic Pricing Models**.\n"
                    "The exam includes **Multiple Choice Questions (MCQs)**, **True/False statements**, and **Short Scenario Analysis**.\n\n"
                    "---\n"
                    "**Question 1/40 (MCQ):**\n"
                    "Which pricing strategy involves setting a high initial price to target price-insensitive early adopters before gradually lowering it?\n"
                    "A) Penetration Pricing\n"
                    "B) Price Skimming\n"
                    "C) Cost-Plus Pricing\n"
                    "D) Freemium Pricing\n\n"
                    "*Reply with your choice (A, B, C, or D) or your full explanation.*"
                ),
            }
        ]

    # Display past conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # -------------------------------------------------------------
    # 5. USER INPUT & 40-QUESTION MIXED ASSESSMENT ORCHESTRATION
    # -------------------------------------------------------------
    if user_prompt := st.chat_input("Type your answer or option letter here..."):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Master mixed-format assessment prompt
        assessment_prompt = f"""
You are an academic examiner conducting a 40-question exam on STRATEGIC PRICING MODELS for student roll number {st.session_state.student_roll}.

TOPICS COVERED:
Cost-Plus, Value-Based, Price Skimming, Penetration, Freemium, Dynamic/Surge, Tiered/Feature-based, Bundling, Loss-Leader, Psychological Pricing, and SaaS Pricing Metrics.

QUESTION DISTRIBUTION (TOTAL 40 QUESTIONS):
- Questions 1 to 15: Multiple Choice Questions (MCQs with 4 options: A, B, C, D).
- Questions 16 to 25: True or False questions (require the student to state True/False and give a 1-sentence justification).
- Questions 26 to 40: Short Concept, Scenario-based, or Numerical/Margin questions.

WORKFLOW RULES:
1. EVALUATION: For every answer submitted by the student:
   - State whether the student's answer was Correct, Partially Correct, or Incorrect.
   - Provide a brief 1-2 sentence explanation of the correct concept.
   - Award a score out of 5 for that question (e.g., Score: 5/5).
2. PROGRESSION:
   - Clearly state the counter for the next question (e.g., "**Question [X]/40 ([Type]):**").
   - If Question 1-15: Always output 4 clean options (A, B, C, D).
   - If Question 16-25: Clearly prompt for True or False.
   - If Question 26-40: Present a focused business scenario or calculation.
3. COMPLETION:
   - When Question 40 is evaluated, do NOT ask any more questions.
   - Output the final consolidated scorecard (Total Marks out of 200), overall percentage, key conceptual strengths, and areas for improvement.
"""

        # Build full conversation history for multi-turn awareness
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
      st.markdown(ai_reply)
    st.session_state.messages.append(
        {'role': 'assistant', 'content': ai_reply}
    )
