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
  if 'messages' not in st.session_state:
    st.session_state.messages = []

  # Display past conversation
  for message in st.session_state.messages:
    with st.chat_message(message['role']):
      st.markdown(message['content'])

  # Student types their response/answer
  if user_prompt := st.chat_input('Type your answer here...'):
    st.session_state.messages.append(
        {'role': 'user', 'content': user_prompt}
    )
    with st.chat_message('user'):
      st.markdown(user_prompt)

    # Generate response from Gemini securely on the server
    with st.spinner('AI is evaluating...'):
      try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_prompt,
            config={
                'system_instruction': (
                    'You are a strict academic assessor conducting an'
                    ' assessment for student roll number'
                    f' {st.session_state.student_roll}. Evaluate their answers'
                    ' objectively.'
                )
            },
        )
        ai_reply = response.text
      except Exception as e:
        ai_reply = (
            'f"Error details: {str(e)}"'
        )

    with st.chat_message('assistant'):
      st.markdown(ai_reply)
    st.session_state.messages.append(
        {'role': 'assistant', 'content': ai_reply}
    )
