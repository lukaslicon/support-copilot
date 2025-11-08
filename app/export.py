# Copyright Lukas Licon 2025. All Rights Reserved.

from typing import List
from .state import ActionPlan, ActionStep, ToolResult
from .tools import TOOLS

def execute_plan(plan: ActionPlan) -> List[ToolResult]:
    results: List[ToolResult] = []
    for step in plan.steps:
        schema, impl = TOOLS[step.tool]
        args = schema(**step.args)
        try:
            out = impl(args)
            results.append(ToolResult(tool=step.tool, ok=True, result=out))
        except Exception as e:
            results.append(ToolResult(tool=step.tool, ok=False, error=str(e), result=None))
    return results
