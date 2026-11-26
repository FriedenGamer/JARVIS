
import streamlit as st
from datetime import date

st.set_page_config(
    page_title="JARVIS AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# ---------- SESSION DATA ----------
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"task": "Complete project UI", "done": False},
        {"task": "Review team progress", "done": True},
        {"task": "Prepare project demo", "done": False}
    ]

if "notes" not in st.session_state:
    st.session_state.notes = []

if "approvals" not in st.session_state:
    st.session_state.approvals = [
        {"action": "Send project update email", "status": "Pending"},
        {"action": "Schedule team meeting", "status": "Pending"}
    ]

if "history" not in st.session_state:
    st.session_state.history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- HEADER ----------
st.title("🤖 JARVIS")
st.caption("Your Personal AI Chief of Staff")
st.divider()

# ---------- EIGHT TABS ----------
tabs = st.tabs([
    "💬 Chat",
    "📧 Inbox",
    "🛡️ Approval Queue",
    "📅 Calendar",
    "💰 Wallet",
    "📋 Weekly Plan",
    "📝 Personal Notes",
    "📊 Activity History"
])

# 1. CHAT
with tabs[0]:
    st.header("Talk to JARVIS")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Ask JARVIS something...")

    if prompt:
        st.session_state.messages.append({
            "role": "user", "content": prompt
        })

        reply = (
            "I received your request: " + prompt +
            ". My AI backend is not connected yet."
        )

        st.session_state.messages.append({
            "role": "assistant", "content": reply
        })

        st.session_state.history.append("Chat: " + prompt)
        st.rerun()

# 2. INBOX
with tabs[1]:
    st.header("Email Inbox")

    emails = [
        ("College Team", "Project meeting tomorrow", "Important"),
        ("Hackathon Team", "JARVIS progress update", "Normal"),
        ("System", "Weekly activity summary", "Normal")
    ]

    for sender, subject, priority in emails:
        with st.container(border=True):
            st.subheader(subject)
            st.write("From:", sender)
            st.write("Priority:", priority)
            if st.button("View email", key=subject):
                st.info("This is sample email content.")

# 3. APPROVAL QUEUE
with tabs[2]:
    st.header("Pending Approvals")
    st.write("Review proposed actions before they are carried out.")

    for i, item in enumerate(st.session_state.approvals):
        if item["status"] == "Pending":
            with st.container(border=True):
                st.write(item["action"])

                col1, col2 = st.columns(2)

                if col1.button("Approve", key=f"approve{i}"):
                    item["status"] = "Approved"
                    st.session_state.history.append(
                        "Approved: " + item["action"]
                    )
                    st.rerun()

                if col2.button("Reject", key=f"reject{i}"):
                    item["status"] = "Rejected"
                    st.session_state.history.append(
                        "Rejected: " + item["action"]
                    )
                    st.rerun()

    for item in st.session_state.approvals:
        if item["status"] != "Pending":
            st.write(item["action"], "-", item["status"])

# 4. CALENDAR
with tabs[3]:
    st.header("Calendar & Schedule")

    selected_date = st.date_input("Choose a date", date.today())
    event = st.text_input("Add an event")

    if st.button("Add event"):
        if event:
            st.session_state.history.append(
                f"Calendar event planned: {event} on {selected_date}"
            )
            st.success("Demo event recorded in activity history.")

# 5. WALLET
with tabs[4]:
    st.header("Bills & Expenses")

    col1, col2, col3 = st.columns(3)
    col1.metric("Monthly Budget", "₹20,000")
    col2.metric("Sample Expenses", "₹8,500")
    col3.metric("Remaining", "₹11,500")

    st.subheader("Upcoming Bills")
    st.write("Internet Bill — ₹799")
    st.write("Mobile Bill — ₹399")
    st.caption("All financial figures are sample data.")

# 6. WEEKLY PLAN
with tabs[5]:
    st.header("Weekly Tasks")

    new_task = st.text_input("Enter a new task")

    if st.button("Add task"):
        if new_task:
            st.session_state.tasks.append({
                "task": new_task,
                "done": False
            })
            st.rerun()

    for i, task in enumerate(st.session_state.tasks):
        checked = st.checkbox(
            task["task"],
            value=task["done"],
            key=f"task{i}"
        )
        task["done"] = checked

    completed = sum(t["done"] for t in st.session_state.tasks)
    total = len(st.session_state.tasks)

    st.progress(completed / total if total else 0)
    st.write(f"{completed} of {total} tasks completed")

# 7. PERSONAL NOTES
with tabs[6]:
    st.header("Personal Notes")

    note = st.text_area("Write your note")

    if st.button("Save note"):
        if note.strip():
            st.session_state.notes.append(note)
            st.success("Note saved for this session.")

    for i, saved_note in enumerate(st.session_state.notes):
        st.text_area(
            f"Saved Note {i + 1}",
            value=saved_note,
            height=80,
            disabled=True
        )

# 8. ACTIVITY HISTORY
with tabs[7]:
    st.header("Activity History")

    if st.session_state.history:
        for activity in reversed(st.session_state.history):
            st.write("•", activity)
    else:
        st.info("No activity recorded yet.")

    st.caption("Demo activity log. Persistent audit storage comes later.")
