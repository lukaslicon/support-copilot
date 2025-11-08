# Copyright Lukas Licon 2025. All Rights Reserved.

from pydantic import BaseModel, Field
from typing import List, Literal
from langchain_openai import ChatOpenAI

class IntentLabel(BaseModel):
    intents: List[str] = Field(description="billing, access, bug, feature, outage")
    severity: Literal["low","normal","high"]

llm = ChatOpenAI(model="gpt-4o-mini")  # swap your model/provider

def classify(text: str) -> IntentLabel:
    classifier = llm.with_structured_output(IntentLabel)
    return classifier.invoke({"input": text})