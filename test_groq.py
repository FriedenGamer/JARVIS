import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()                                   # reads the .env file
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

reply = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Say hello in one line"}],
)
print(reply.choices[0].message.content)