# Copyright Lukas Licon 2025. All Rights Reserved.
import os
from pydantic import BaseModel, Field
from typing import List, Literal
from langchain_openai import ChatOpenAI

class IntentLabel(BaseModel):
    intents: List[str] = Field(description="billing, access, bug, feature, outage")
    severity: Literal["low", "normal", "high"]

def get_llm():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it or create a .env file.")
    return ChatOpenAI(model="gpt-4o-mini", api_key=key)

def classify(text: str) -> IntentLabel:
    llm = get_llm()
    classifier = llm.with_structured_output(IntentLabel)
    # ❗️Pass a STRING, not {"input": ...}
    return classifier.invoke(text)
