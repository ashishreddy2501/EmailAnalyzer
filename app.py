import streamlit as st
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="Inbox Explorer", page_icon="📩")

# --- 1. AUTHENTICATION ---
if not st.user.is_logged_in:
    st.title("📩 Organization Email Assistant")
    st.write("Log in to analyze specific emails from your inbox.")
    if st.button("Log in with Google"):
        st.login()
    st.stop()

# --- 2. INITIALIZATION ---
try:
    creds = Credentials(token=st.user.access_token)
    gmail_service = build('gmail', 'v1', credentials=creds)
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Initialization Error: {e}")
    st.stop()

# --- 3. UI CONTROLS ---
st.sidebar.title(f"Logged in as")
st.sidebar.info(st.user.email)

# USER INPUT: Choose which email to read
st.sidebar.divider()
st.sidebar.subheader("Search Settings")
email_index = st.sidebar.number_input(
    "Which email should I read? (1 = Latest)", 
    min_value=1, 
    max_value=50, 
    value=1,
    help="1 is your most recent email, 2 is the one before that, and so on."
)

st.title("Email Summary Dashboard")
st.write(f"Currently looking at email **#{email_index}** in your Inbox.")

# --- 4. FETCH AND ANALYZE ---
if st.button(f"Analyze Email #{email_index}", type="primary"):
    with st.spinner(f"Fetching email #{email_index}..."):
        # We fetch enough messages to reach the index requested
        results = gmail_service.users().messages().list(
            userId='me', 
            labelIds=['INBOX'], 
            maxResults=email_index 
        ).execute()
        
        messages = results.get('messages', [])
        
        if len(messages) >= email_index:
            # Select the specific message based on the user's input (adjusting for 0-index)
            target_msg_id = messages[email_index - 1]['id']
            msg = gmail_service.users().messages().get(userId='me', id=target_msg_id).execute()
            
            snippet = msg.get('snippet', 'No content available.')
            
            # UI Feedback
            st.subheader(f"Content of Email #{email_index}")
            st.info(snippet)
            
            # --- GEMINI ANALYSIS ---
            with st.spinner("Gemini is analyzing..."):
                prompt = f"Summarize this email for {st.user.name}. Focus on action items: {snippet}"
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                
                st.subheader("AI Insight")
                st.success(response.text)
        else:
            st.warning(f"You don't have {email_index} emails in your inbox. Try a smaller number.")

if st.sidebar.button("Logout"):
    st.logout()
