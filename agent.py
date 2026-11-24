import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MOCK_MODE = os.getenv("MOCK_LLM", "false").lower() == "true"


def ask_llm(kind, messages=None):
    """Return the AI's reply. In mock mode, read a saved reply instead."""
    if MOCK_MODE:
        with open("data/mock_responses.json", "r") as f:
            saved = json.load(f)
        return saved[kind]

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL"),
        messages=messages,
    )
    return response.choices[0].message.content
