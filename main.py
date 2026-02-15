from fastapi import FastAPI, HTTPException
from google import genai
import os
from dotenv import load_dotenv

# =========================
# Load ENV
# =========================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ New Gemini Client (NEW SDK)
client = genai.Client(api_key=API_KEY)

# =========================
# FastAPI App
# =========================
app = FastAPI(title="Fitness Gemini Chatbot")

# =========================
# Dummy User Activity Data
# =========================
dummy_user = {
    "name": "Prasad",
    "weight": "80kg",
    "goal": "Fat Loss + Muscle Gain",
    "daily_steps": 6500,
    "workout_time": "1.5 hours",
    "focus_area": "Chest Fat Reduction"
}

# =========================
# Allowed Topics Checker
# =========================
def is_allowed_question(question: str):
    fitness_keywords = [
        "fitness", "gym", "workout", "diet", "protein",
        "exercise", "cardio", "steps", "health",
        "fat", "muscle", "activity", "calories"
    ]

    q = question.lower()
    return any(word in q for word in fitness_keywords)

# =========================
# GET API
# =========================

@app.get("/chat")
async def fitness_chat(prompt: str):

    # 🔒 Hard Filter
    if not is_allowed_question(prompt):
        return {
            "response": "I only answer fitness and user activity related questions."
        }

    # =========================
    # System Prompt
    # =========================
    system_prompt = f"""
You are a STRICT Fitness AI Assistant.

RULES:
- Answer ONLY fitness, workout, diet, health or user activity questions.
- If question is unrelated, say:
  "I only answer fitness and activity related questions."

USER DATA:
Name: {dummy_user["name"]}
Weight: {dummy_user["weight"]}
Goal: {dummy_user["goal"]}
Daily Steps: {dummy_user["daily_steps"]}
Workout Duration: {dummy_user["workout_time"]}
Focus Area: {dummy_user["focus_area"]}

Give short practical answers.
"""

    try:
        # ✅ NEW GEMINI CALL
        response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=system_prompt + "\nUser Question: " + prompt
    )

        return {"response": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
