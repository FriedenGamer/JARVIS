import os
import json
from dotenv import load_dotenv
from groq import Groq
from guardrails import get_risk, validate_call

load_dotenv()

MOCK_MODE = os.getenv("MOCK_LLM", "false").lower() == "true"
MAX_STEPS = 5


def ask_llm(email_id, messages=None):
    """Return the AI's reply. In mock mode, read a saved reply instead."""
    if MOCK_MODE:
        with open("data/mock_responses.json", "r") as f:
            saved = json.load(f)
        return saved[email_id]

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL"),
        messages=messages,
    )
    return response.choices[0].message.content


def run_tool(tool, args):
    """TEMPORARY fake tool runner. Manhith's tools.py replaces this later."""
    return {"success": True, "data": {"tool": tool, "args": args}, "error": None}


def process_email(email):
    """Run the agent loop for one email. Stops after MAX_STEPS."""
    steps = 0
    last_tool = None

    while steps < MAX_STEPS:
        steps += 1
        decision = ask_llm(email["id"])
        tool = decision["tool"]

        if tool == "ask_user":
            return {"status": "needs_info", "question": decision["args"]["question"]}

        if tool == last_tool:
            return {"status": "stopped", "message": "I repeated the same tool, so I stopped."}

        ok, problem = validate_call(tool, decision["args"])
        if not ok:
            return {"status": "rejected", "message": problem}

        risk = get_risk(tool)

        if risk == "high":
            return {
                "status": "pending",
                "tool": tool,
                "args": decision["args"],
                "reason": decision["reason"],
                "message": "Waiting for your approval.",
            }

        last_tool = tool
        result = run_tool(tool, decision["args"])
        return {"status": "done", "tool": tool, "result": result, "reason": decision["reason"]}

    return {"status": "stopped", "message": "Too many steps, so I stopped."}


if __name__ == "__main__":
    with open("data/emails.json", "r") as f:
        emails = json.load(f)
    for email in emails:
        print("Email:", email["subject"])
        print("Outcome:", process_email(email))
        print()