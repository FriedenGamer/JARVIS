import streamlit as st

st.set_page_config(
    page_title="JARVIS AI Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("JARVIS")
st.caption("Your Personal AI Chief of Staff")

tabs = st.tabs([
    "Chat",
    "Inbox",
    "Approval Queue",
    "Calendar",
    "Wallet",
    "Weekly Plan",
    "Notes",
    "Audit Log"
])
