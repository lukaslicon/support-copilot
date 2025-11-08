# Copyright Lukas Licon 2025. All Rights Reserved.

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from .state import CaseState, DraftReply

llm = ChatOpenAI(model="gpt-4o-mini")

_prompt = ChatPromptTemplate.from_messages([
  ("system", "Use ONLY the snippets provided. Cite claims using [n] markers referencing snippet indices. If info is missing, ask for it briefly."),
  ("user", "Ticket:\n{ticket}\n\nSnippets:\n{snippets}\n\nWrite a clear, empathetic reply.")
])

def draft_reply(state: CaseState):
    snippets = [f"[{i}] {c.text}\n({c.source})" for i, c in enumerate(state["retrieved"], start=1)]
    chain = _prompt | llm | StrOutputParser()
    md = chain.invoke({"ticket": state["ticket"].text, "snippets":"\n".join(snippets)})
    return DraftReply(ticket_id=state["ticket"].id, markdown=md,
                      citations=[c.source for c in state["retrieved"]])