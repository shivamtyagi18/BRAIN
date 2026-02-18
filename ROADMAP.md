# 🧠 Brain System — Roadmap

Future enhancements organized by priority. Pick one, build it, ship it.

---

## 🔥 High Impact — Architecture

- [ ] **Vector Memory** — Replace JSON keyword-search with embedding-based retrieval (ChromaDB/FAISS)
- [ ] **Streaming Responses** — Stream tokens from Executive Agent in real-time (SSE in web UI)
- [ ] **Async Agents** — True async LLM calls for the 3 parallel agents to cut latency
- [ ] **Custom Agents** — Let developers add/remove/replace agents in the pipeline

## ⚡ Medium Impact — Features

- [ ] **Agent Weighting** — Adjustable influence per agent ("be more logical, less emotional")
- [ ] **Conversation History** — Pass previous exchanges to agents, not just memory retrieval
- [ ] **Multi-modal Input** — Accept images/audio alongside text via the Sensory Agent
- [ ] **Callbacks/Hooks** — `on_sensory_complete`, `on_before_executive`, etc. for monitoring
- [ ] **More Agents** — Creativity Agent, Social Agent, Moral Reasoning Agent, Metacognition Agent

## 🛠 Medium Impact — Developer Experience

- [ ] **Telemetry/Logging** — Structured logging with per-agent timing
- [ ] **Config File Support** — YAML/TOML config as alternative to constructor params
- [ ] **Test Suite** — Unit tests with mocked LLM calls (zero tests currently)
- [ ] **CI/CD Pipeline** — GitHub Actions for auto-test, build, and publish on release tags

## 🌱 Long-term — Ambitious

- [ ] **Learning/Adaptation** — Agents adapt prompts over time based on user feedback
- [ ] **Multi-turn Persona** — Persona evolves during conversation, not just static extraction
- [ ] **Agent-to-Agent Debate** — Logic vs Emotional back-and-forth before Executive synthesizes
- [ ] **Tool Use** — Give agents external tools (web search, calculator, code execution)
