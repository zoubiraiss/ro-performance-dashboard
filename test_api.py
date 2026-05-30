from dotenv import load_dotenv
import google.generativeai as genai
import os

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model_names = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-pro"
]

for name in model_names:
    try:
        model = genai.GenerativeModel(name)
        response = model.generate_content("Hello")
        print(f"✅ {name} works!")
        break
    except Exception as e:
        print(f"❌ {name} failed")