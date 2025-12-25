import google.generativeai as genai

genai.configure(api_key="AIzaSyBRl1tbv45iW55dSN7g7u6_yQ12JYF7ebk")  # Replace with your Gemini API key

# List all available models
models = genai.list_models()
for model in models:
    print(model.name)