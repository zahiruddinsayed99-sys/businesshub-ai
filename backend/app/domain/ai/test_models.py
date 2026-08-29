import os
import google.generativeai as genai
from dotenv import load_dotenv

# This automatically loads your .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: Could not find GEMINI_API_KEY in your .env file!")
    exit()

# Configure the SDK
genai.configure(api_key=api_key)

print("\n--- Available Gemini Models for Text Generation ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Failed to connect to Google API: {e}")
print("---------------------------------------------------\n")