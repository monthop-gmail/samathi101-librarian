import os
import google.generativeai as genai

KEY = os.environ.get("GEMINI_API_KEY")
print(f"API Key present: {bool(KEY)}")
if KEY:
    print(f"Key Prefix: {KEY[:7]}...")
    genai.configure(api_key=KEY)
    try:
        print("Listing models...")
        for m in genai.list_models():
            print(f"Model: {m.name} (Methods: {m.supported_generation_methods})")
    except Exception as e:
        print(f"Error: {e}")
