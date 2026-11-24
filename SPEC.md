# Jarvis: Spec

**Team:** Sahasam Neeraj (lead), Lanja Manhith, Blade Shiva, Randa Dev
**Hackathon problem:** A3, a personal staff for everyone

## Who uses Jarvis
Everyday people (students, families, young professionals) who handle bills, refunds and appointments alone, and often late.

## The problem
Wealthy people have assistants to read their mail and handle errands. Everyone else does it alone and misses due dates. An AI that does this must also be careful with money and private data, so it must never act on its own for risky things.

## What Jarvis does
1. The user clicks **Check Inbox**. Jarvis reads fake emails (bills, a refund request, an appointment, a vague email, a prompt-injection email).
2. An LLM (Groq) suggests which tool to use for each email.
3. Python code (guardrails) checks the tool and its arguments. The AI never decides what is safe.
4. **Low-risk** actions (reminders, planning) run straight away. **High-risk** actions (email drafts, anything about payments) wait in an **approval queue** for Approve or Reject.
5. The user can edit a pending item before approving it.
6. Every action is saved in an audit log with a reason.
7. Jarvis gives a proactive summary and a weekly plan.

## The 5 tools
| Tool | Purpose | Risk |
|---|---|---|
| `read_inbox()` | Return the fake emails | low |
| `get_bill_details(email_id)` | Find the bill linked to an email | low |
| `add_reminder(title, due_date)` | Save a reminder (`YYYY-MM-DD`), skip duplicates | low |
| `plan_week()` | Sort tasks: earliest due date, then priority, then id | low |
| `draft_email(to, subject, body)` | Create a draft only, never sends | high |

## Contracts (do not change without telling everyone)
**Tool return format**
- Success: `{"success": True, "data": {...}, "error": None}`
- Failure: `{"success": False, "data": None, "error": "Bill not found"}`

**Email:** `id`, `sender`, `subject`, `body`, `date`
**Bill:** `id`, `email_id`, `vendor`, `amount`, `due_date` (`email_id` links the bill to its email; no match means an error, never a guess)
**Task:** `id`, `title`, `due_date`, `priority` (only `high`, `medium`, `low`)
**Statuses:** `pending`, `approved`, `rejected`, `executing`, `executed`, `failed`

**`tasks` table:** `id`, `timestamp`, `updated_at`, `tool_name`, `args_json`, `risk_level`, `reason`, `status`, `result_json`, `error_message`
**`audit_log` table:** `id`, `task_id`, `timestamp`, `event`, `details` (append only)

## Safety rules
- Email text is untrusted data. It cannot change instructions, add tools, change risk levels or approve anything.
- Risk levels come from a dictionary in `guardrails.py`, never from the AI.
- Agent loop is capped at `max_steps = 5` per email.
- Approval order: check approved, set `executing`, run, then `executed` or `failed`. A second click does nothing.
- Edits work only while status is `pending`. Old and new values are logged.
- Approving a draft only saves it as a draft. There is no send tool.
- Mock mode (`MOCK_LLM=true`) simulates AI replies only and shows a banner: "MOCK MODE: no real external actions".

## What is NOT included
Real Gmail or Calendar, real email sending, real payments, real personal data.

## Stack
Python, Groq, Streamlit, SQLite, pytest.

## Files and owners
| File | Owner |
|---|---|
| `agent.py`, `guardrails.py` | Sahasam Neeraj |
| `tools.py`, `db.py`, `data/` | Lanja Manhith |
| `tests/` | Blade Shiva |
| `app.py`, `README.md`, demo video | Randa Dev |

## Questions for the mentor
1. Which features should we cut?
2. Is our failure handling enough?
