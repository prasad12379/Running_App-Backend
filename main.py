from fastapi import FastAPI, HTTPException
from google import genai
import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, db
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime
from fastapi import Query

import json


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
# 🔥 Firebase Setup (NEW)
# =========================

firebase_json = os.getenv("FIREBASE_CREDENTIALS")
cred_dict = json.loads(firebase_json)
cred = credentials.Certificate(cred_dict)

# ✅ SAFE INITIALIZATION
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://calorix-3939c-default-rtdb.firebaseio.com/"
    })

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


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
    

import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)



# =========================
# 📦 Signup Request Model
# =========================

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: int
    gender: str
    height: float
    weight: float


def make_safe_email(email: str):
    return email.replace("@", "_").replace(".", "_")


# =========================
# ✅ Signup API (NEW)
# =========================

@app.post("/signup")
async def signup(user: SignupRequest):

    safe_email = make_safe_email(user.email)

    ref = db.reference(f"Users/{safe_email}")

    # Check existing user
    if ref.get():
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash password
    hashed_password = pwd_context.hash(user.password)

    user_data = {
    "name": user.name,
    "email": user.email,
    "password_hash": hashed_password,
    "age": user.age,
    "gender": user.gender,
    "height": user.height,
    "weight": user.weight,
    "created_at": datetime.utcnow().isoformat(),

    # ⭐ NEW SECTION (EMPTY OBJECT)
    "activity": {}
}


    ref.set(user_data)

    return {
        "message": "Signup successful",
        "user_id": safe_email
    }


# =========================
# 📦 Signin Request Model
# =========================
class SigninRequest(BaseModel):
    email: EmailStr
    password: str

# =========================
# ✅ Signin API
# =========================
@app.post("/signin")
async def signin(user: SigninRequest):

    safe_email = make_safe_email(user.email)

    ref = db.reference(f"Users/{safe_email}")
    user_data = ref.get()

    # ❌ User not found
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    stored_hash = user_data.get("password_hash")

    # ❌ Password mismatch
    if not pwd_context.verify(user.password[:72], stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ Successful Login
    return {
        "message": "Signin successful",
        "user_id": safe_email,
        "name": user_data.get("name"),
        "email": user_data.get("email")
    }


@app.get("/user")
async def get_user(email: str = Query(...)):

    # convert email → safe firebase key
    safe_email = make_safe_email(email)

    ref = db.reference(f"Users/{safe_email}")
    user_data = ref.get()

    # ❌ user not found
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # ⚠️ NEVER send password hash to frontend
    user_data.pop("password_hash", None)

    return {
        "message": "User data fetched successfully",
        "data": user_data
    }