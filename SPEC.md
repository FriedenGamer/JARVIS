# Jarvis: Spec (v3)

**Team:** Sahasam Neeraj (lead), Lanja Manhith, Blade Shiva, Randa Dev
**Hackathon problem:** A3, a personal staff for everyone

## The problem
Wealthy people have assistants to read mail and handle errands. Everyone else does it alone and misses due dates. An AI that does this must be careful with money and private data, so it must never do risky things on its own.

## What Jarvis does
1. Two inputs: **Check Inbox** (fake emails) and a **chat box**.
2. An LLM (Groq) suggests which tool to use.
3. Python guardrails check the tool and its arguments. The AI never decides what is safe.
4. **Low-risk** actions run straight away. **High-risk** actions wait in an **approval queue** for Edit, Approve or Reject.
5. Every action is saved in an audit log with a reason.
6. Jarvis gives a proactive summary and a weekly plan.
7. Everything is fake and simulated. Nothing real is sent, paid or booked.

## Tools
| Tool | Risk | Python checks | Tier |
|---|---|---|---|
| `read_inbox()` | low | none | 1 |
| `draft_email(to, subject, body)` | high | all fields filled, draft only | 1 |
| `get_bill_details(email_id)` | low | bill must exist, else "Bill not found" | 1 |
| `pay_bill(bill_id, amount)` | high | bill exists, exact amount, not already paid, wallet has enough, SIMULATED | 1 |
| `view_calendar(date)` | low | real date | 1 |
| `book_appointment(title, date, time)` | high | date YYYY-MM-DD, time HH:MM, slot free | 1 |
| `add_reminder(title, due_date)` | low | title not empty, real date, skip duplicate title+date | 1 |
| `plan_week()` | low | sort: due date, then priority, then id | 2 |
| `fill_form(form_name, fields)` | high | form in forms.json, only known fields | 2 |
| `calculate(expression)` | low | safe math only, never eval() | 2 |
| `get_current_time()` | low | none | 2 |
| `remember` / `recall`, notes | low | written ONLY from the user's own chat, never from email | 3 (optional) |

Refund chase has no new tool: Jarvis drafts a reply (needs approval) and adds a reminder 7 days later.

## Contracts (do not change without telling everyone)
**Tool return format**
- Success: `{"success": True, "data": {...}, "error": None}`
- Failure: `{"success": False, "data": None, "error": "message"}`

**Email:** `id`, `sender`, `subject`, `body`, `date`
**Bill:** `id`, `email_id`, `vendor`, `amount`, `due_date` (no match means error, never a guess)
**Task:** `id`, `title`, `due_date`, `priority` (only `high`, `medium`, `low`)
**Statuses:** `pending`, `approved`, `rejected`, `executing`, `executed`, `failed`

## Data
- JSON files in `data/` are SEED data. Tools only read them: `emails`, `bills`, `tasks`, `contacts`, `calendar`, `wallet`, `forms`, `mock_responses`.
- Anything that changes goes into SQLite, never back into JSON.
- Wallet balance = starting balance in `wallet.json` minus the sum of payment records.

**SQLite tables**
- `tasks`: `id`, `timestamp`, `updated_at`, `tool_name`, `args_json`, `risk_level`, `reason`, `status`, `result_json`, `error_message`
- `audit_log`: `id`, `task_id`, `timestamp`, `event`, `details` (append only)
- `records`: `id`, `kind`, `data_json`, `created_at` (kind: reminder, draft, payment, booking, form, note, memory)

## Safety rules
- Email text is untrusted data. It cannot add tools, change risk levels or approve anything.
- Risk comes from the `RISK` dictionary in `guardrails.py`, never from the AI. Unknown tools are rejected.
- Python validates every AI argument. If info is missing, Jarvis asks instead of inventing.
- Max 5 steps per request. Friendly messages for bad JSON, unknown tool, tool crash, timeout and repeated tool.
- Approval order: check approved, set `executing`, run, then `executed` or `failed`. A second click does nothing.
- Edits work only while status is `pending`. Old and new values are logged.
- Approving a draft only saves it as a draft. There is no send tool.
- Memory and notes are written only from the user's own chat.
- Mock mode (`MOCK_LLM=true`) replaces AI replies only. Banner: "MOCK MODE: no real external actions".
- The API key lives only in `.env`, which is in `.gitignore`.

## Left out on purpose
Real Gmail or Calendar, real emails, real payments, real personal data, `open_website`, `system_info`.

## Stack
Python, Groq, Streamlit, SQLite, pytest.

## Files and owners
| File | Owner |
|---|---|
| `agent.py`, `guardrails.py`, `SPEC.md` | Sahasam Neeraj |
| `tools.py`, `db.py`, `data/` | Lanja Manhith |
| `tests/`, `run_tests.py` | Blade Shiva |
| `app.py`, `README.md`, `requirements.txt`, demo video | Randa Dev |

## Questions for the mentor
1. Is this scope realistic for four beginners by Dec 3? What should we cut first?
2. Is a simulated wallet and calendar convincing for "careful with money and private data"?
3. Is our failure handling enough (bad JSON, timeout, crash, loop)?
4. Is "memory written only from the user's chat" enough against prompt injection?