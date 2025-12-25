import google.generativeai as genai

genai.configure(api_key="AIzaSyBguCDDUeWfEL5Bx-2szhAAznQ9jLvanRo")

models = genai.list_models()

for model in models:
    print(f"Model name: {model.name}")
    print(f"  Description: {model.description}")
    print(f"  Supported generation methods: {model.supported_generation_methods}")
    print("--------------------------------------------------")
