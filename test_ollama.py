import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434/v1/"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL"
)

print("Ollama host:", OLLAMA_HOST)
print("Model:", OLLAMA_MODEL)

client = OpenAI(
    base_url=OLLAMA_HOST,
    api_key="ollama"
)

start = time.time()

response = client.chat.completions.create(
    model=OLLAMA_MODEL,
    temperature=0,
    messages=[
        {
            "role": "user",
            "content": "In one sentence, explain what a consulting firm does."
        }
    ]
)

elapsed = time.time() - start

print("\nMODEL RESPONSE:\n")
print(response.choices[0].message.content)

print(f"\nTIME TAKEN: {elapsed:.2f} seconds")