import json
import sqlite3
import streamlit as st
import agent
import approval
import tools
import db

db.init_db()

# Page configuration
st.set_page_config(
    page_title="JARVIS AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
.stApp {
    background-color: #0b1020;
    color: white;
}
h1, h2, h3 {
    color: #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# Header
st.title("🤖 JARVIS")
st.caption("YOUR PERSONAL AI CHIEF OF STAFF")
if getattr(agent, "MOCK_MODE", False):
    st.info("MOCK MODE: no real external actions")

# Sidebar
with st.sidebar:
    st.title("JARVIS")
    st.caption("AI COMMAND CENTER")
    st.divider()

    st.write("🟢 System Status: Online")
    engine_label = "Mock LLM" if getattr(agent, "MOCK_MODE", False) else "Groq (llama-3.3-70b-versatile)"
    st.write(f"🧠 AI Engine: {engine_label}")
    st.write("🛡️ Safety: Enabled")

    st.divider()
    st.write("Developed by Team JARVIS")


def fetch_audit_events():
    try:
        conn = db._connect()
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


# Navigation
tabs = st.tabs([
    "💬 Chat",
    "📧 Inbox",
    "✅ Approval Queue",
    "📅 Calendar",
    "💰 Wallet",
    "📋 Weekly Plan",
    "📝 Notes",
    "📊 Audit Log"
])

# TAB 1: CHAT
with tabs[0]:
    st.header("Talk to JARVIS")
    st.write("How can I assist you today?")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_input = st.chat_input("Ask JARVIS anything...")

    if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        with st.chat_message("user"):
            st.write(user_input)

        res = agent.process_chat(user_input)
        status = res.get("status")

        if status == "done":
            reply = str(res.get("result", "Done."))
        elif status == "pending":
            reply = f"Queued for approval (Task #{res.get('task_id')})"
        elif status == "needs_info":
            reply = str(res.get("question", "More details needed."))
        elif status == "error":
            reply = str(res.get("message", "Something went wrong."))
        else:
            reply = json.dumps(res, indent=2)

        st.session_state.messages.append({
            "role": "assistant",
            "content": reply
        })
        with st.chat_message("assistant"):
            st.write(reply)

# TAB 2: INBOX
with tabs[1]:
    st.header("Email Inbox")
    inbox_res = tools.read_inbox()
    emails = inbox_res.get("data", []) if inbox_res.get("success") else []

    if emails:
        st.dataframe(emails, use_container_width=True)
    else:
        st.info(inbox_res.get("error") or "No emails in inbox.")

    if st.button("Check Inbox"):
        if not emails:
            st.warning("No emails found to process.")
        else:
            for email in emails:
                email_id = email.get("id", "unknown")
                subject = email.get("subject", "No subject")
                out = agent.process_email(email)
                st.write(f"**{email_id} — {subject}:** `{json.dumps(out)}`")

# TAB 3: APPROVAL QUEUE
with tabs[2]:
    st.header("Approval Center")
    st.write("Review actions before execution.")

    pending = db.list_tasks(status="pending")
    if not pending:
        st.info("No pending tasks in the Approval Queue.")
    else:
        for task in pending:
            task_id = task.get("id")
            st.divider()
            st.subheader(f"Task #{task_id} — `{task.get('tool_name')}`")
            st.write(f"**Risk Level:** `{task.get('risk_level')}`")
            st.write(f"**Reason:** {task.get('reason')}")

            raw_args = task.get("args_json", task.get("args", {}))
            if isinstance(raw_args, str):
                default_args_str = raw_args
            else:
                default_args_str = json.dumps(raw_args, indent=2)

            edited_text = st.text_area(
                f"Arguments (JSON) — Task #{task_id}",
                value=default_args_str,
                height=110,
                key=f"args_{task_id}"
            )

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Save Edit", key=f"edit_{task_id}"):
                    try:
                        parsed_args = json.loads(edited_text)
                        approval.edit_task(task_id, parsed_args)
                        st.success(f"Updated Task #{task_id}")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Invalid JSON: {exc}")

            with col2:
                if st.button("Approve", key=f"approve_{task_id}"):
                    approval.approve_and_run(task_id)
                    st.rerun()

            with col3:
                if st.button("Reject", key=f"reject_{task_id}"):
                    approval.reject_task(task_id)
                    st.rerun()

# TAB 4: CALENDAR
with tabs[3]:
    st.header("Calendar")
    selected_date = st.date_input("Select date", value=st.session_state.get("cal_date"))
    st.session_state["cal_date"] = selected_date
    date_str = selected_date.isoformat()

    cal_res = tools.view_calendar(date_str)
    st.subheader(f"Appointments on {date_str}")
    if cal_res.get("success"):
        st.dataframe(cal_res.get("data", []), use_container_width=True)
    else:
        st.info(cal_res.get("error") or "No calendar items.")

    st.subheader("Active Reminders")
    reminders = db.list_records("reminders")
    if reminders:
        st.dataframe(reminders, use_container_width=True)
    else:
        st.info("No active reminders.")

# TAB 5: WALLET
with tabs[4]:
    st.header("Digital Wallet")
    with open("data/wallet.json", "r", encoding="utf-8") as f:
        wallet_cfg = json.load(f)
    with open("data/bills.json", "r", encoding="utf-8") as f:
        bills_cfg = json.load(f)

    starting_balance = float(wallet_cfg.get("starting_balance", 0))
    currency = wallet_cfg.get("currency", "INR")
    paid_bills = db.list_records("bills")

    paid_total = 0.0
    paid_ids = set()
    for rec in paid_bills:
        data_part = rec.get("data", rec) if isinstance(rec, dict) else {}
        if isinstance(data_part, str):
            try:
                data_part = json.loads(data_part)
            except Exception:
                data_part = {}
        amt = float(data_part.get("amount", 0) or 0)
        paid_total += amt
        if data_part.get("bill_id"):
            paid_ids.add(data_part["bill_id"])

    live_balance = starting_balance - paid_total
    st.metric("Wallet Balance", f"{currency} {live_balance:,.2f}")
    st.caption("All payments are simulated.")

    bill_rows = []
    for b in bills_cfg:
        b_id = b.get("id")
        bill_rows.append({
            "id": b_id,
            "vendor": b.get("vendor"),
            "amount": b.get("amount"),
            "due_date": b.get("due_date"),
            "status": "paid" if b_id in paid_ids else "unpaid"
        })
    st.subheader("Bills Status")
    st.dataframe(bill_rows, use_container_width=True)

# TAB 6: WEEKLY PLAN
with tabs[5]:
    st.header("Weekly Plan")
    if st.button("Generate Weekly Plan"):
        st.session_state["weekly_plan_res"] = tools.plan_week()

    plan_res = st.session_state.get("weekly_plan_res")
    if plan_res is None:
        plan_res = tools.plan_week()

    if plan_res.get("success"):
        st.dataframe(plan_res.get("data", []), use_container_width=True)
    else:
        st.error(plan_res.get("error") or "Could not generate weekly plan.")

# TAB 7: NOTES
with tabs[6]:
    st.header("Tasks & Scratchpad (Read-Only)")
    with open("data/tasks.json", "r", encoding="utf-8") as f:
        tasks_data = json.load(f)
    st.dataframe(tasks_data, use_container_width=True)

# TAB 8: AUDIT LOG
with tabs[7]:
    st.header("Activity History")
    st.subheader("Tasks")
    all_tasks = db.list_tasks()
    if all_tasks:
        st.dataframe(all_tasks, use_container_width=True)
    else:
        st.info("No tasks recorded yet.")

    st.subheader("Audit Log Events")
    audit_events = fetch_audit_events()
    if audit_events:
        st.dataframe(audit_events, use_container_width=True)
    else:
        st.info("No append-only audit events found.")
