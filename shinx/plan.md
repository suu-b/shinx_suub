# Migration Guide: `update_state` Fake Tool → LangGraph `Command` Pattern

> **Scope:** Orchestrator and Optimizer agent nodes in Shinx.  
> **LangGraph version:** 1.2.16 (installed)  
> **No code changes in this document** — this is a planning reference only.

---

## 1. What `Command` Is (from the Installed Source)

`Command` is a frozen dataclass in `langgraph.types` (line 833 of `types.py` in your venv):

```python
# langgraph/types.py (your installed v1.2.16)
@dataclass(frozen=True, slots=True)
class Command(Generic[N]):
    graph:  str | None                       = None   # None = this graph; Command.PARENT = parent graph
    update: Any | None                       = None   # dict of state updates (same shape as returning from a node)
    resume: dict[str, Any] | Any | None      = None   # only for resuming after interrupt()
    goto:   Send | Sequence[Send | N] | N    = ()     # node name(s) or Send objects to route to
```

**Import:**
```python
from langgraph.types import Command
```

---

## 2. The Core Mental Model Shift

### Before — Fake Tool Pattern

```
orchestrator node runs
  └─ LLM decides to call update_state(key="current_agent", value="optimizer")
       └─ Tool returns "Updated current_agent to optimizer"  ← a lie
  └─ agent_node post-processes tool call args manually:
       updates["current_agent"] = "optimizer"
  └─ returns {"messages": [...], "current_agent": "optimizer"}

graph reads current_agent → conditional edge → routes to optimizer
```

**Problems:**
- Tool doesn't actually update anything — it lies to the LLM
- Manual scraping of `tool_call.get('args')` is fragile
- Logic is duplicated in both `orchestration/agent.py` and `orchestration/agents/optimizer.py`
- Routing is a separate step (conditional edge) that the LLM can't control atomically

### After — Command Pattern

```
orchestrator node runs
  └─ LLM produces its output (structured or parsed)
  └─ agent_node reads desired next node from the output
  └─ returns Command(
         goto="optimizer",
         update={"task_type": "optimize", "agent_status": "running", "messages": new_msgs}
     )

LangGraph atomically updates state AND routes to optimizer — no conditional edge needed
```

**Benefits:**
- State update and routing happen in one atomic operation
- No fake tools, no arg scraping
- Graph topology is simpler (fewer edges)
- LLM doesn't need to call a tool to signal routing — it can express intent in structured output or plain text that the node parses

---

## 3. Graph Topology Change

### Before (current `graph.py`)

```python
workflow.add_edge(START, "orchestrator")
workflow.add_conditional_edges(
    "orchestrator",
    route_from_orchestrator,       # reads state["current_agent"]
    {"optimizer": "optimizer", "END": END},
)
workflow.add_edge("optimizer", "orchestrator")
```

### After (with Command)

```python
workflow.add_edge(START, "orchestrator")
# No conditional edges needed — orchestrator returns Command(goto=...)
workflow.add_edge("optimizer", "orchestrator")
```

> ⚠️ **LangGraph doc warning:** Do NOT mix `Command(goto=...)` from a node with static `add_conditional_edges` on the same node. Pick one mechanism. Since `orchestrator` will use `Command`, remove `add_conditional_edges` for it. The `optimizer → orchestrator` static edge stays because optimizer doesn't need to control routing.

---

## 4. The Two Approaches for the Orchestrator

The orchestrator needs to tell the graph *which agent to go to next*. With `Command`, the node function itself returns that decision. There are two ways to extract the decision from the LLM:

### Option A — Structured Output (Recommended)

Bind the LLM to output a Pydantic schema that includes `next_agent`. This is the cleanest approach and requires no tool calls at all for routing.

```python
from pydantic import BaseModel
from typing import Literal

class OrchestratorDecision(BaseModel):
    reasoning: str
    next_agent: Literal["optimizer", "END"]
    task_type: str | None = None
    agent_status: Literal["pending", "running", "completed", "failed"] = "running"

# In create_agent_node:
llm_with_structure = self.llm.with_structured_output(OrchestratorDecision)
```

The node then calls the structured LLM and reads `decision.next_agent` directly — no tool call parsing needed.

### Option B — Keep `create_react_agent`, parse last AIMessage content

If you want to keep the ReAct loop (so the orchestrator can still call investigation tools), you parse the **final AIMessage content** for a routing decision (e.g., JSON embedded in the response, or a dedicated small `@tool` that returns a `Command`).

> For Shinx's current use case (orchestrator only routes, doesn't investigate), **Option A** is cleaner. For a future orchestrator that also calls tools before routing, **Option B** or a hybrid is more appropriate.

---

## 5. File-by-File Implementation Plan

### 5.1 `orchestration/agent.py` — OrchestratorAgent

**Remove:**
- The `@tool def update_state(...)` definition
- The `for msg in new_messages` loop that scrapes `tool_call.get('args')`
- The `**updates` spread in the return dict

**Add:**
- LLM structured output binding (`llm.with_structured_output(OrchestratorDecision)`)
- Parse `decision.next_agent` from the structured output
- Return `Command(goto=next_node, update={...state fields...})`

**New `agent_node` sketch:**

```python
def agent_node(state: BaseState) -> Command[Literal["optimizer", "__end__"]]:
    messages = ensure_user_turn(list(state["messages"]))
    
    # Call LLM with structured output — no fake tool needed
    decision: OrchestratorDecision = llm_structured.invoke(messages)
    
    # Map "END" sentinel to LangGraph's END constant name
    goto = "__end__" if decision.next_agent == "END" else decision.next_agent
    
    return Command(
        goto=goto,
        update={
            "task_type":     decision.task_type or state.get("task_type"),
            "agent_status":  decision.agent_status,
            "current_agent": decision.next_agent,
            "iterations":    state["iterations"] + 1,
            # messages: only append an AI explanation if desired
        }
    )
```

> **Note on `goto` with END:** LangGraph uses the string `"__end__"` or the `END` constant (`"__end__"` is its value). You can `from langgraph.graph import END` and use `END` directly in `Command(goto=END)`.

**Return type annotation** (required by LangGraph for graph rendering):
```python
def agent_node(state: BaseState) -> Command[Literal["optimizer", "__end__"]]:
```

---

### 5.2 `orchestration/agents/optimizer.py` — OptimizerAgent

**Remove:**
- `@tool def update_state(...)` definition
- `@tool def complete_agent(results: str)` definition — the truncation bug goes with it
- The entire `for msg in new_messages` scraping loop
- `**updates` spread

**Keep:**
- `create_react_agent(...)` with the investigation tools (`explain_query`, `inspect_table`, etc.)
- The Gemini tail-append guard
- The prior-count slice for new messages

**Add:**
- After `agent.invoke()`, parse the **last AIMessage** for the final result JSON (the optimizer already formats it as JSON in its prompt). The node should not rely on a tool call side-effect to capture results.
- Return `Command` to update `agent_results` and `agent_status`, then go back to `"orchestrator"`.

**New return:**

```python
# Extract result from final message content (optimizer always outputs JSON summary)
final_msg = new_messages[-1]
result_str = final_msg.content if hasattr(final_msg, "content") else ""

return Command(
    goto="orchestrator",   # always returns to orchestrator
    update={
        "messages":      new_messages,
        "agent_results": {"output": result_str},
        "agent_status":  "completed",
        "iterations":    state["iterations"] + 1,
    }
)
```

> Alternatively, keep a real (non-fake) `complete_agent` tool that returns `Command` directly from inside the tool — this is supported in LangGraph 1.2+ via `ToolOutputMixin`. The `Command` class already extends `ToolOutputMixin` in the installed version (line 833: `class Command(Generic[N], ToolOutputMixin)`).

---

### 5.3 `orchestration/graph.py` — build_orchestration_graph

**Remove:**
- `route_from_orchestrator()` function entirely
- `workflow.add_conditional_edges(...)` call for orchestrator

**Keep:**
- `workflow.add_edge(START, "orchestrator")`
- `workflow.add_edge("optimizer", "orchestrator")`

The orchestrator node's `Command(goto=...)` is now the sole routing mechanism out of the orchestrator.

---

### 5.4 `core/state.py` — BaseState (minor)

`current_agent` can be kept for observability/logging (the orchestrator's `Command.update` can still write it), but it is no longer *required* for routing. The field remains useful for the prompt to tell agents what state they're in.

---

## 6. OrchestratorDecision Schema Design

```python
from pydantic import BaseModel, Field
from typing import Literal

class OrchestratorDecision(BaseModel):
    """Structured output for the orchestrator's routing decision."""
    
    reasoning: str = Field(
        description="Brief explanation of why this routing decision was made"
    )
    next_agent: Literal["optimizer", "END"] = Field(
        description="Which agent to dispatch next. Use END when the task is complete."
    )
    task_type: Literal["optimize", "generate", "implement"] | None = Field(
        default=None,
        description="Type of task. Set on first call, leave None to keep existing."
    )
    agent_status: Literal["pending", "running", "completed", "failed"] = Field(
        default="running",
        description="Status to set on the state."
    )
```

As more agents are added (e.g., `query_generator`, `implementation`), extend the `Literal` union for `next_agent`.

---

## 7. Prompt Update for the Orchestrator

The orchestrator prompt currently instructs the LLM to *call* `update_state(key="current_agent", value="optimizer")`. With structured output, the prompt changes to instruct the LLM to *output* the routing decision directly.

**Key changes to `orchestrator_prompt.py`:**
- Remove the `## Your Tools / update_state(key, value)` section entirely
- Add a section explaining the output schema (`OrchestratorDecision`)
- Change "call `update_state`" phrasing to "return your decision in the structured format"

**Suggested new section:**

```
## Your Output

You must respond in the structured format provided. Key fields:

- `reasoning`: A brief, internal explanation of your decision.
- `next_agent`: The agent to dispatch. Options:
  - "optimizer" — analyze a SQL query for performance issues
  - "END" — the task is complete, stop the workflow
- `task_type`: Set this on your first response based on the user's intent.
- `agent_status`: Use "running" when dispatching an agent, "completed" when done.
```

---

## 8. `complete_agent` — Two Clean Alternatives

The current `complete_agent` tool is fake and truncates results. Two clean replacements:

### Alt A: Remove it, parse final message content
The optimizer's system prompt already instructs it to output a JSON summary as its final response. The node reads `new_messages[-1].content` directly. No tool needed.

### Alt B: Real `Command`-returning tool (advanced)
Since `Command` extends `ToolOutputMixin`, a tool can return a `Command` object that LangGraph will interpret as a real graph control directive:

```python
@tool
def complete_optimizer(results: str) -> Command:
    """Signal optimizer completion and return results to the graph."""
    return Command(
        goto="orchestrator",
        update={
            "agent_results": {"output": results},
            "agent_status": "completed",
        }
    )
```

This is the most elegant form — the tool is honest (it genuinely updates state), the graph routes immediately on tool completion, and no post-processing is needed in the node. Use this if you want to keep `create_react_agent` for the optimizer.

---

## 9. Implementation Order

1. **Add `OrchestratorDecision` Pydantic model** (new file `models/orchestrator.py` or inline in `orchestration/agent.py`)
2. **Update `orchestration/agent.py`** — replace fake tool with structured output + `Command` return
3. **Update `orchestration/graph.py`** — remove conditional edge, keep static edges
4. **Update `orchestration/agents/optimizer.py`** — remove fake tools, add `Command` return (or `complete_optimizer` real tool)
5. **Update `prompts/orchestrator_prompt.py`** — remove `update_state` instructions, add structured output instructions
6. **Test** with `test_orchestrator.py`

---

## 10. Key Gotchas

| Gotcha | Detail |
|---|---|
| **Don't mix `Command` and `add_conditional_edges` on the same node** | Both will fire, causing double routing. Remove the conditional edge when the node returns `Command`. |
| **`goto=END` vs `goto="__end__"`** | Both work. `from langgraph.graph import END` gives you `"__end__"` as a string constant. Use `END` for clarity. |
| **Return type annotation is required** | `-> Command[Literal["optimizer", "__end__"]]` — LangGraph needs this for graph validation and rendering. |
| **`Command.update` respects reducers** | If `messages` has `add_messages` reducer, putting `"messages": new_msgs` in `Command.update` works correctly — it won't double-append. |
| **Structured output + Gemini** | `llm.with_structured_output(OrchestratorDecision)` works with `ChatGoogleGenerativeAI`. The Gemini tail-append guard is no longer needed for the orchestrator if you switch to structured output (no chat history is sent in the same way). For the optimizer which still uses `create_react_agent`, the guard stays. |
| **`current_agent` state field** | Keep it in `BaseState` — write it via `Command.update` for observability. It's just not used for routing anymore. |
