# Copyright Lukas Licon 2025. All Rights Reserved.

from .state import ToolResult, ActionPlan
from typing import List
from .tools import refund_tool

def execute_plan(plan: ActionPlan) -> List[ToolResult]:
    results = []
    for step in plan.steps:
        try:
            if step.tool == "refund":
                res = refund_tool.invoke(step.args)  # call the LangChain tool
                results.append(ToolResult(tool=step.tool, ok=True, result=res))
            else:
                results.append(ToolResult(tool=step.tool, ok=False, error="Tool not implemented"))
        except Exception as e:
            results.append(ToolResult(tool=step.tool, ok=False, error=str(e)))
    return results