"""
Streamlit UI for the 3GPP RAG Assistant

Calls the FastAPI backend at http://localhost:8000

Run:
    streamlit run src/frontend/app.py

Requires the FastAPI backend to be running:
    uvicorn src.api.main:app --reload --port 8000
"""
import json
import time
import requests
import streamlit as st

API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="3GPP RAG Assistant",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        color: #888;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .source-card {
        background: #1e1e2e;
        border-left: 3px solid #4f8ef7;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }
    .similarity-badge {
        background: #2a4a7f;
        color: #9ec5fe;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .timing-bar {
        color: #888;
        font-size: 0.8rem;
        margin-top: 0.4rem;
    }
    .status-ok    { color: #4ade80; }
    .status-warn  { color: #facc15; }
    .status-error { color: #f87171; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def init_state():
    defaults = {
        "session_id": None,
        "messages": [],          # [{role, content, sources, timing}]
        "api_online": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def check_api() -> dict:
    """Call /health and return the response dict, or {} on failure."""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.json()
    except Exception:
        return {}


def post_query(question: str, source_filter: str, top_k: int) -> dict:
    """POST /query and return parsed JSON."""
    payload = {
        "question": question,
        "session_id": st.session_state.session_id,
        "source_filter": source_filter or None,
        "top_k": top_k,
    }
    r = requests.post(f"{API_BASE}/query", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def stream_query(question: str, source_filter: str, top_k: int):
    """
    POST /query/stream and yield parsed SSE chunks.
    Yields dicts: {type: sources|token|done|error, ...}
    """
    payload = {
        "question": question,
        "session_id": st.session_state.session_id,
        "source_filter": source_filter or None,
        "top_k": top_k,
    }
    with requests.post(
        f"{API_BASE}/query/stream",
        json=payload,
        stream=True,
        timeout=120,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line and line.startswith(b"data: "):
                yield json.loads(line[6:])


def get_stats() -> dict:
    try:
        r = requests.get(f"{API_BASE}/stats", timeout=5)
        return r.json()
    except Exception:
        return {}


def clear_session_history():
    if st.session_state.session_id:
        try:
            requests.delete(
                f"{API_BASE}/history/{st.session_state.session_id}",
                timeout=5,
            )
        except Exception:
            pass
    st.session_state.messages = []
    st.session_state.session_id = None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    # API status
    health = check_api()
    if health.get("status") == "ok":
        st.session_state.api_online = True
        st.markdown('<span class="status-ok">● API Online</span>', unsafe_allow_html=True)
    elif health.get("status") == "degraded":
        st.session_state.api_online = True
        st.markdown('<span class="status-warn">● API Degraded</span>', unsafe_allow_html=True)
    else:
        st.session_state.api_online = False
        st.markdown('<span class="status-error">● API Offline</span>', unsafe_allow_html=True)
        st.warning("Start the API:\n```\nuvicorn src.api.main:app --reload\n```")

    st.divider()

    # Query settings
    st.markdown("### Query Settings")
    top_k = st.slider("Chunks to retrieve", min_value=1, max_value=15, value=5)
    source_filter = st.text_input(
        "Filter by document",
        placeholder="e.g. 38300",
        help="Only retrieve chunks from documents whose filename contains this string",
    )
    use_streaming = st.toggle("Streaming mode", value=True,
                              help="Stream tokens as they are generated")

    st.divider()

    # Component health detail
    if health.get("components"):
        st.markdown("### Component Status")
        icons = {"ok": "✅", "degraded": "⚠️", "unavailable": "❌"}
        for name, info in health["components"].items():
            icon = icons.get(info.get("status", "unavailable"), "❓")
            st.markdown(f"{icon} **{name}**: {info.get('detail', '')}")

    st.divider()

    # Session controls
    st.markdown("### Session")
    if st.session_state.session_id:
        st.caption(f"ID: `{st.session_state.session_id[:16]}...`")
    if st.button("🗑️ Clear conversation", use_container_width=True):
        clear_session_history()
        st.rerun()

    # Stats panel
    if st.session_state.api_online:
        with st.expander("📊 Performance Stats"):
            s = get_stats()
            if s:
                m = s.get("metrics", {})
                if m.get("total_queries", 0) > 0:
                    st.metric("Total queries", m["total_queries"])
                    st.metric("Avg total time",
                              f"{m['total_time']['mean']:.2f}s")
                    st.metric("Avg retrieve time",
                              f"{m['retrieve_time']['mean']:.2f}s")
                    st.metric("Avg generate time",
                              f"{m['generate_time']['mean']:.2f}s")
                    vs = s.get("vector_store", {})
                    st.metric("Chunks indexed",
                              vs.get("total_chunks", "—"))
                else:
                    st.caption("No queries recorded yet.")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.markdown('<div class="main-header">📡 3GPP RAG Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Ask questions about 3GPP specifications — '
    'fully local, zero cost, cited answers</div>',
    unsafe_allow_html=True,
)

# Example query chips
example_queries = [
    "What is the gNB-CU architecture?",
    "Explain the F1 interface",
    "How does handover work in 5G?",
    "What is the difference between SA and NSA?",
]

cols = st.columns(len(example_queries))
for col, q in zip(cols, example_queries):
    if col.button(q, use_container_width=True):
        st.session_state["pending_question"] = q

st.divider()

# ---------------------------------------------------------------------------
# Render existing messages
# ---------------------------------------------------------------------------

def render_sources(sources: list):
    if not sources:
        return
    with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
        for s in sources:
            st.markdown(
                f'<div class="source-card">'
                f'<b>{s["source"]}</b> '
                f'<span class="similarity-badge">{s["similarity"]:.0%}</span><br>'
                f'<small>{s["text"][:250]}{"..." if len(s["text"]) > 250 else ""}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_sources(msg.get("sources", []))
            if msg.get("timing"):
                t = msg["timing"]
                st.markdown(
                    f'<div class="timing-bar">⏱ total={t["query_time"]}s '
                    f'| retrieve={t["retrieve_time"]}s '
                    f'| generate={t["generate_time"]}s</div>',
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------------------------
# Handle input
# ---------------------------------------------------------------------------

# Pick up question from example chip or text input
question = st.chat_input(
    "Ask a question about 3GPP specs...",
    disabled=not st.session_state.api_online,
)
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    if not st.session_state.api_online:
        st.error("API is offline. Start it with: `uvicorn src.api.main:app --reload`")
        st.stop()

    # Show user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Generate answer
    with st.chat_message("assistant"):
        if use_streaming:
            # Streaming path
            token_placeholder = st.empty()
            sources = []
            full_answer = []
            timing = {}

            try:
                for chunk in stream_query(question, source_filter, top_k):
                    if chunk["type"] == "sources":
                        sources = chunk.get("sources", [])
                        # Update session_id from next done chunk — handled below
                    elif chunk["type"] == "token":
                        full_answer.append(chunk["token"])
                        token_placeholder.markdown("".join(full_answer) + "▌")
                    elif chunk["type"] == "done":
                        token_placeholder.markdown("".join(full_answer))
                        timing = {
                            "query_time": chunk.get("query_time", 0),
                            "retrieve_time": 0,
                            "generate_time": chunk.get("query_time", 0),
                        }
                        if chunk.get("session_id"):
                            st.session_state.session_id = chunk["session_id"]
                    elif chunk["type"] == "error":
                        st.error(chunk.get("detail", "Unknown streaming error"))
                        st.stop()

                answer = "".join(full_answer)

            except Exception as e:
                st.error(f"Streaming error: {e}")
                st.stop()

        else:
            # Blocking path
            with st.spinner("Searching specifications..."):
                try:
                    result = post_query(question, source_filter, top_k)
                except requests.HTTPError as e:
                    st.error(f"API error: {e}")
                    st.stop()
                except Exception as e:
                    st.error(f"Request failed: {e}")
                    st.stop()

            answer = result["answer"]
            sources = result.get("sources", [])
            timing = {
                "query_time": result["query_time"],
                "retrieve_time": result["retrieve_time"],
                "generate_time": result["generate_time"],
            }
            st.session_state.session_id = result["session_id"]
            st.markdown(answer)

        render_sources(sources)
        st.markdown(
            f'<div class="timing-bar">⏱ total={timing.get("query_time", 0):.2f}s</div>',
            unsafe_allow_html=True,
        )

    # Save to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "timing": timing,
    })
