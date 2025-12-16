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
    system_prompt = """
    You are acting as a scam and fraud detection assistant.

    Rules:
    - Always respond in valid JSON.
    - Do NOT include any text outside the JSON.
    - The "model" field MUST be set to "gpt-4o-mini".
    - Summarize the intent and context of the received message in "message_summary".
    - Only flag scams when there is reasonable suspicion.
    - Consider whether the message could realistically lead the receiver to:
        (a) transfer money,
        (b) share personal or account-related information,
        (c) act under urgency, fear, or authority pressure.
    - Hypothesize plausible malicious scenarios even if not explicitly stated. 
    - Include these plausible scenarios in both "risk_reason" and "user_warning".
    
    Style guidelines for "user_warning":
    - Write in first-person singular ("I").
    - Mention who sent the message, if identifiable.
    - Briefly describe what the message is about.
    - Include a specific plausible fraud scenario.
    - Explain why it could be risky in a calm, non-accusatory tone.
    - Sound like a helpful assistant speaking directly to the user.
    - If risk_level is LOW, set "user_warning" exactly to: "All Good".

    Required JSON schema:
    {
      "model": string,
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