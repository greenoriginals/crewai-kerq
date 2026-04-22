# crewai-kerq

**Kerq trust scoring and telemetry for CrewAI agent workflows.**

Every tool your agent touches has a trust score. `crewai-kerq` lets you check it before connecting — and automatically reports execution telemetry back to Kerq for continuous monitoring.

Get your API key at [kerq.dev](https://kerq.dev).

---

## Installation

```bash
pip install crewai-kerq
```

Or with `uv`:

```bash
uv add crewai-kerq
```

---

## Components

### `KerqTrustTool` — Check trust scores on demand

An agent tool that checks a tool's Kerq trust score. Drop it into any agent's tool list.

```python
from crewai import Agent, Task, Crew
from crewai_kerq import KerqTrustTool

kerq = KerqTrustTool(api_key="your-api-key")

agent = Agent(
    role="Security Analyst",
    goal="Verify tool safety before use",
    backstory="You check tool trust scores before connecting to anything.",
    tools=[kerq],
)

task = Task(
    description="Check the trust score for 'github-mcp'",
    expected_output="Trust score and tier for github-mcp",
    agent=agent,
)

crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
```

---

### `KerqTelemetryHandler` — Automatic execution telemetry

Hooks into CrewAI's event bus and reports tool execution latency and status to Kerq after every tool call. Fire-and-forget — never blocks your agent.

```python
from crewai import Agent, Task, Crew
from crewai_kerq import KerqTelemetryHandler

# Instantiate once — auto-registers on the CrewAI event bus
handler = KerqTelemetryHandler(api_key="your-api-key")

agent = Agent(
    role="Data Researcher",
    goal="Gather market intelligence",
    backstory="Expert researcher with access to search tools.",
    tools=[...],  # your tools here
)

task = Task(
    description="Research the latest AI trends",
    expected_output="Summary of AI trends",
    agent=agent,
)

crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
# Tool telemetry automatically reported to Kerq after each tool call
```

To disable telemetry:

```python
handler = KerqTelemetryHandler(api_key="your-api-key", telemetry=False)
```

---



### `KerqGuard` — Trust gating + telemetry in one

Blocks tools below your minimum trust score AND reports telemetry. The safest option for production agents.

```python
from crewai import Agent, Task, Crew
from crewai_kerq import KerqGuard

# Instantiate once — auto-registers on the CrewAI event bus
guard = KerqGuard(
    api_key="your-api-key",
    min_score=70,      # block any tool scoring below 70
    telemetry=True,    # also report execution telemetry
)

agent = Agent(
    role="Autonomous Agent",
    goal="Complete tasks safely",
    backstory="You only use trusted tools.",
    tools=[...],
)

task = Task(
    description="Do work with verified tools only",
    expected_output="Completed task",
    agent=agent,
)

crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
# Any tool scoring below 70 raises PermissionError at runtime
# Successful tool calls report telemetry to Kerq
```

**Deterministic behaviour on bad data:**
- Missing, null, or unparseable trust scores are treated as `0` and **blocked**.
- 401 (invalid API key) or 429 (rate limit) → guard skips the check, logs a warning, does NOT block.
- Network errors → score treated as `0`, tool blocked.

---

## Configuration

All three components take the same constructor arguments:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `api_key` | `str` | *(required)* | Your Kerq API key from [kerq.dev](https://kerq.dev) |
| `min_score` | `int` | `70` | *(KerqGuard only)* Minimum acceptable trust score (0–100) |
| `telemetry` | `bool` | `True` | Enable/disable telemetry reporting |

---

## How it works

- **Trust scores** are fetched from `https://kerq.dev/api/tools/{tool_id}/score`
- **Telemetry** is posted to `https://kerq-mcp.polsia.app/v1/report` with `tool_id`, `status_code`, and `latency_ms`
- All HTTP calls have a hard 2-second timeout
- Telemetry is fire-and-forget — never raises, never blocks your agent

---

## Requirements

- Python 3.10+
- `crewai >= 0.80.0`
- `httpx >= 0.25.0`

---

## License

MIT — see [LICENSE](./LICENSE).

---

## Links

- Website: [kerq.dev](https://kerq.dev)
- Docs: [kerq.dev/docs](https://kerq.dev/docs)
- Issues: [github.com/greenoriginals/crewai-kerq/issues](https://github.com/greenoriginals/crewai-kerq/issues)

