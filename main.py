from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
import json

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

@app.get("/")
def root():
    return {"message": "TheCatcher backend is running!"}

# # Request schema (what Android sends, the caught push notification from social medias)
class AnalyzeRequest(BaseModel):
    sender: str
    text: str



# Response schema (what Android receives from OpenAI)
class AnalyzeResponse(BaseModel):
    model: str
    sender: str
    message_summary: str
    risk_level: str
    risk_reason: str
    user_warning: str


@app.post("/analyze/", response_model=AnalyzeResponse)
def analyze_message(request: AnalyzeRequest):
    system_prompt = f"""
    You are acting as a scam and fraud detection assistant.

    Rules:
    - Always respond in valid JSON.
    - Do NOT include any text outside the JSON.
    - All string values in the JSON must be written in {request.userLanguage}, regardless of the language of the incoming message.
    - Summarize the intent and context of the received message in "message_summary".
    - Consider whether the message could realistically lead the receiver to:
        (a) transfer money,
        (b) share personal or account-related information,
        (c) act under abnormal or manipulated emotional influence
    - Consider the contemporary digital threat landscape and evolving scam techniques.
    - Focus on risks that may not be immediately obvious to the user, including potential account compromise, impersonation, or other digital threats.
    - Only flag scams when there is reasonable suspicion.
    - When risk_level is assessed as LOW, write the reason in "risk_reason".
    - When risk_level is assessed as HIGH, provide a concise scenario explaining the reason and generate "user_warning" accordingly.
    
    Style guidelines for "user_warning":
    - If risk_level is LOW, set "user_warning" exactly to: "All Good".
    - If risk_level is HIGH:
        (a) Use first-person singular, speaking as the assistant addressing the user (e.g., "I see you received…").
        (b) Mention who sent the message, if identifiable.
        (c) Briefly describe what the message is about.
        (d) Use a concrete scenario to show why the message is high risk.
        (e) Explain the risk through this scenario calmly and objectively.
        (f) Sound like a calm, rational friend.
        (e) Limit "user_warning" to fewer than 30 words.

    Required JSON schema:
    {
      "sender": string,
      "message_summary": string,
      "risk_level": "LOW" | "HIGH",
      "risk_reason": string,
      "user_warning": string
    }
    """
    user_prompt = f"""
    Sender: {request.sender}
    Message content: {request.text}
    """

    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=system_prompt,
        input=user_prompt,
        temperature = 0.2,
        max_output_tokens = 300 #1 token ≈ 4 characters; 1 token ≈ ¾ of a word
    )

    # manually parse JSON output
    try:
        result = json.loads(response.output_text)
    except json.JSONDecodeError:
        result = {"error": "Failed to parse JSON from LLM response", "raw_output": response.output_text}

    return result