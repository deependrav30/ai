# TODO for Collaborative Agent System

## Must-Have Features (from requirements)

1. Implement Retrieval-Augmented Generation (RAG)
   - Retrieval before generation
   - Separate retrieval, reasoning, response synthesis
   - Reference retrieved context in responses
   - Index Word, PDF, TXT, PPTX, images (with OCR)
2. Implement document chunking & overlap strategy
   - Configurable chunk size and overlap
   - Justify chunking choices
3. Build context management system
   - Manage short-term context
   - Prevent unbounded growth (summarization, windowing, pruning)
4. Implement explicit memory types
   - Working, Episodic, Semantic
   - Agents read/write memory
5. Ensure memory persistence
   - Persist across requests
   - UI for view/modify/delete memory
6. Build Guardrails & Safety agent
   - Confidence thresholds
   - "I don't know" handling
   - Escalation policies
   - Block violence, self-harm, sexual, hate, jailbreak attempts
7. Implement Planning & Delegation agent
   - At least one agent plans execution
   - Delegate tasks to agents
   - Each agent in separate file/module
8. Enable explicit tool/function usage
   - Agents call retrieval, memory, policy tools
   - Log tool input, execution, results
   - UI live streams agent calls, steps, outputs
   - Display agent interactions in UI
9. Add observability & explainability
   - Show which agents ran
   - Show what data was used
   - Show why decisions were made

## Agents to Implement
- Ingestion Agent
- Planner / Orchestrator Agent
- Intent & Classification Agent
- Knowledge Retrieval Agent (RAG)
- Memory Agent
- Reasoning / Correlation Agent
- Response Synthesis Agent
- Guardrails & Policy Agent

## Execution Model
- Demonstrate serial, parallel, and async agent execution

## Additional Steps
- Design project folder structure
- Select agent framework (LangGraph/CrewAI/ADK)
- Build document upload/storage system
- Develop customer chatbot UI (3 tabs)
- Implement session/context management
- Build employee dashboard for incident visibility
- Integrate RAG pipeline with agent flows
- Add observability/live agent event streaming
- Test with 100+ multi-page documents
- Perform QA and monitoring
