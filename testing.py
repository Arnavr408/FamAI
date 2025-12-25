import google.generativeai as genai

import google.generativeai
print(google.generativeai.__file__)


# Configure API key
genai.configure(api_key="AIzaSyBguCDDUeWfEL5Bx-2szhAAznQ9jLvanRo")

# Initialize the Gemini-Pro model (v1)
model = genai.GenerativeModel("models/gemini-2.0-flash")

# Ask a question
response = model.generate_content("Decide whether this query needs a web search to answer it accurately. "
        "Answer ONLY with YES or NO. Do NOT explain.\nQuery: Tell me a joke")

# Print the response
print("Answer:", response.text.strip())
