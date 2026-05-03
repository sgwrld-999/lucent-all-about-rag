"""Agent node for the Page RAG workflow."""

from __future__ import annotations

from accelerate import state
from langchain_core.messages import SystemMessage

from lucent.config  import llm

from lucent.states import PageRAGState
from lucent.tools import retrieve_docs_tool

def agent_node(PageRAGState):
    messages = state["messages"]
    llm_with_tools = llm.bind_tools([retrieve_docs_tool])

    system_prompt = """You are a financial document analysis assistant with access to a document retrieval tool.

CRITICAL RULES:
1. ALWAYS use the retrieve_docs tool first; NEVER answer from memory.
2. You MUST call the tool before providing financial information.
3. Answer ONLY based on retrieved documents.
4. If documents do not contain the answer, state that clearly.

WORKFLOW:
- For simple questions: call retrieve_docs once, then answer with citations.
- For comparison questions: split by entity, call retrieve_docs per entity, then compare in a table.

OUTPUT FORMAT:
- Use Markdown headings.
- Use bullet points for key takeaways.
- Use tables for comparisons.
- Always include citations with company/year/quarter/page when available.
"""

    system_msg = SystemMessage(content=system_prompt)
    response = llm_with_tools.invoke([system_msg] + messages)

    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            print(
                f"[AGENT] called Tool {tool_call.get('name', '?')} "
                f"with args {tool_call.get('args', '?')}"
            )
    else:
        print("[AGENT] Responding...")

    return {"messages": [response]}

    return agent_node
