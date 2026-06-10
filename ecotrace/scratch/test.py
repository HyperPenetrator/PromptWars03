import os
import json
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    system_instruction='''You are EcoTrace, a friendly and knowledgeable carbon footprint coach.
Respond in this JSON structure:
{
  "summary": "1–2 sentence overview",
  "top_emission": {"category": "...", "co2e_kg": 0.0, "percentage": 0},
  "suggestions": [
    {"action": "...", "potential_saving_kg": 0.0, "difficulty": "easy|medium|hard"}
  ],
  "encouragement": "1 sentence motivational note"
}''',
    generation_config=genai.GenerationConfig(
        temperature=0.7,
        response_mime_type='application/json',
    ),
)
prompt = "Analyze this data and provide personalized suggestions"
response = model.generate_content(prompt)
print('FINISH REASON:', response.candidates[0].finish_reason)
print('RAW TEXT:', repr(response.text))
