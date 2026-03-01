import os
from dotenv import load_dotenv
from google import genai

# Load your GOOGLE_API_KEY from .env
load_dotenv()

# Initialize the Gemini client
client = genai.Client()

# Fetch and print all available models
print("Available Gemini Models:")
print("-" * 30)

for model in client.models.list():
    print(f"- {model.name}")
