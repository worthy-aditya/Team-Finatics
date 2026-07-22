import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="You are a security analyst assistant. In one sentence, "
             "explain why open port 445 (SMB) on a public-facing server is risky."
)

print(response.text)