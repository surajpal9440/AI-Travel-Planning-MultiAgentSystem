import os
import streamlit as st
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from main import app

st.set_page_config(
    page_title="AI Travel Booking System",
    page_icon="✈️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background-color: #080d14;
}

/* ── Hero ── */
.hero-wrapper {
    position: relative;
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 2rem;
    height: 280px;
}
.hero-bg {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    filter: brightness(0.35);
    position: absolute;
    top: 0; left: 0;
}
.hero-content {
    position: relative;
    z-index: 2;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2rem;
}
.hero-badge {
    background: rgba(58,123,213,0.25);
    border: 1px solid rgba(58,123,213,0.5);
    color: #7ab8f5 !important;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    margin-bottom: 0.9rem;
    display: inline-block;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.6rem;
    line-height: 1.2;
}
.hero-sub {
    color: #94adc8;
    font-size: 1rem;
    max-width: 560px;
}

/* ── Chat bubbles ── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.chat-bubble {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    max-width: 80%;
}
.chat-bubble.user { align-self: flex-end; flex-direction: row-reverse; }
.chat-bubble.agent { align-self: flex-start; }
.bubble-avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
}
.bubble-avatar.user  { background: linear-gradient(135deg, #1a6bbf, #0d4a8a); }
.bubble-avatar.agent { background: linear-gradient(135deg, #1e3a5c, #0e2240); border: 1px solid #2a5080; }
.bubble-text {
    padding: 0.75rem 1rem;
    border-radius: 14px;
    font-size: 0.93rem;
    line-height: 1.6;
}
.bubble-text.user  {
    background: linear-gradient(135deg, #1a3a5c, #0e2240);
    border: 1px solid #2a5080;
    color: #cce0f5;
    border-top-right-radius: 4px;
}
.bubble-text.agent {
    background: #0e1623;
    border: 1px solid #1e2e44;
    color: #cce0f5;
    border-top-left-radius: 4px;
}

/* ── Planner status badge ── */
.planner-collecting {
    background: rgba(255, 165, 0, 0.1);
    border: 1px solid rgba(255, 165, 0, 0.3);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin-bottom: 1rem;
    color: #ffc947;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.planner-ready {
    background: rgba(0, 200, 100, 0.1);
    border: 1px solid rgba(0, 200, 100, 0.3);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin-bottom: 1rem;
    color: #4cdb93;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Input card ── */
.input-card {
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.5rem;
}
.input-label {
    color: #7ab8f5;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* ── Quick destinations ── */
.dest-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin: 0.8rem 0 1.2rem;
}
.dest-chip {
    background: #111b2b;
    border: 1px solid #1e3050;
    color: #f7fdf4;
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.2s;
}
.dest-chip:hover { background: #1a2e47; border-color: #3a7bd5; color: #fff; }

/* ── Generate button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1a6bbf 0%, #0d4a8a 50%, #0a3d75 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 2.5rem !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    width: 100% !important;
    box-shadow: 0 0 24px rgba(26,107,191,0.35), 0 4px 15px rgba(0,0,0,0.4) !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stButton"] > button:hover {
    box-shadow: 0 0 40px rgba(26,107,191,0.6), 0 6px 20px rgba(0,0,0,0.5) !important;
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #2278d4 0%, #1057a0 50%, #0d4a8a 100%) !important;
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0px) !important;
}

/* ── Agent status cards ── */
[data-testid="stStatusWidget"] {
    background: #0e1a2e !important;
    border: 1px solid #1e3050 !important;
    border-radius: 12px !important;
}
[data-testid="stStatusWidget"] > div:first-child {
    background: #0e1a2e !important;
    border-radius: 12px 12px 0 0 !important;
}
[data-testid="stStatusWidget"] details,
[data-testid="stStatusWidget"] details > div,
[data-testid="stStatusWidget"] [data-testid="stVerticalBlock"] {
    background: #0a1520 !important;
    color: #ffffff !important;
    padding: 0.25rem 0.5rem !important;
}
[data-testid="stStatusWidget"] * { color: #ffffff !important; }
[data-testid="stStatusWidget"] a { color: #4ea8f0 !important; }
[data-testid="stStatusWidget"] hr { border-color: #1e3050 !important; }

/* ── Section headers ── */
.sec-head {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 2rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e2e44;
}
.sec-head span { font-size: 1.15rem; font-weight: 600; color: #e0edf8; }

/* ── Metric bar ── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin: 1.5rem 0;
}
.metric-box {
    flex: 1;
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-val { font-size: 1.8rem; font-weight: 700; color: #4ea8f0; }
.metric-lbl { font-size: 0.78rem; color: #5a7a96; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Final plan ── */
.final-card {
    background: linear-gradient(160deg, #0c1a2e 0%, #0a1520 100%);
    border: 1px solid #1e3a5c;
    border-left: 4px solid #3a7bd5;
    border-radius: 14px;
    padding: 1.8rem;
    line-height: 1.8;
    color: #cce0f5;
    font-size: 0.95rem;
}

/* ── Save bar ── */
.save-bar {
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 10px;
    padding: 0.85rem 1.2rem;
    color: #5a8ab0;
    font-size: 0.88rem;
    margin-top: 0.5rem;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #090e18 !important;
    border-right: 1px solid #141f30 !important;
}
.sidebar-chip {
    background: #0e1a2b;
    border: 1px solid #1a2e44;
    border-radius: 8px;
    padding: 0.45rem 0.75rem;
    margin-bottom: 0.4rem;
    font-size: 0.83rem;
    color: #7aa8cc;
}
.sidebar-title { color: #e0edf8; font-size: 1rem; font-weight: 600; margin: 1rem 0 0.5rem; }

/* ── Collected info pills ── */
.info-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.5rem;
}
.info-pill {
    background: #0e1a2b;
    border: 1px solid #2a5080;
    color: #7ab8f5;
    font-size: 0.78rem;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
}

/* Hide branding */
#MainMenu, footer, header { visibility: hidden; }

/* Textarea */
.stTextArea textarea {
    background: #0a1520 !important;
    border: 1px solid #1e2e44 !important;
    border-radius: 10px !important;
    color: #e8f4ff !important;
    font-size: 0.95rem !important;
    resize: none !important;
}
.stTextArea textarea:focus {
    border-color: #3a7bd5 !important;
    box-shadow: 0 0 0 2px rgba(58,123,213,0.2) !important;
}
.stTextArea textarea::placeholder { color: #4a6a85 !important; }

/* Text input (sidebar User ID field) */
input[type="text"], .stTextInput input {
    background: #0e1a2b !important;
    border: 1px solid #1a2e44 !important;
    border-radius: 8px !important;
    color: #e0edf8 !important;
}
input[type="text"]:focus, .stTextInput input:focus {
    border-color: #3a7bd5 !important;
    box-shadow: 0 0 0 2px rgba(58,123,213,0.2) !important;
}
input[type="text"]::placeholder { color: #3a5570 !important; }

/* All Streamlit labels — dark bg → light text */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label {
    color: #7ab8f5 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
}

/* General markdown / paragraph text */
.stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th {
    color: #cce0f5 !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #e8f4ff !important; }
.stMarkdown code {
    background: #0e1a2b !important;
    color: #7ab8f5 !important;
    padding: 0.15em 0.4em;
    border-radius: 4px;
}

/* Metric labels */
.metric-lbl { color: #7aa8cc !important; }

/* Save bar */
.save-bar { color: #8ab8d8 !important; }
.save-bar code { color: #7ab8f5 !important; background: #0a1520 !important; }

/* Streamlit warning / info / success on dark bg */
.stAlert { background: #0e1a2b !important; border-radius: 10px !important; }
.stAlert p, .stAlert div { color: #e0edf8 !important; }

/* Sidebar text & dividers */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown { color: #a0c4e0 !important; }
section[data-testid="stSidebar"] hr { border-color: #1a2e44 !important; }

/* Download button */
div[data-testid="stDownloadButton"] > button {
    background: #1a3a5c !important;
    color: #e8f4ff !important;
    border: 1px solid #2a5080 !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []          # list of {"role": "user"|"agent", "content": str}
if "planning_complete" not in st.session_state:
    st.session_state.planning_complete = False
if "collected_info" not in st.session_state:
    st.session_state.collected_info = {}        # source, destination, budget, days
if "final_result" not in st.session_state:
    st.session_state.final_result = None
import random
import string

if "username" not in st.session_state:
    st.session_state.username = "aarohi_user"
if "trip_id" not in st.session_state:
    st.session_state.trip_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div class='sidebar-title'>🌍 AI Travel Planner</div>", unsafe_allow_html=True)
    st.markdown("---")

    new_username = st.text_input("👤 Username", value=st.session_state.username,
                                 help="Your username for the application")
    
    if new_username != st.session_state.username:
        st.session_state.username = new_username
        st.session_state.trip_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
        st.session_state.chat_history = []
        st.session_state.planning_complete = False
        st.session_state.collected_info = {}
        st.session_state.final_result = None
        st.rerun()

    st.markdown("<div class='sidebar-title'>Powered by</div>", unsafe_allow_html=True)
    for tech in ["🔗 LangGraph", "🧠 Groq · LLaMA 3.3 70B", "🐘 PostgreSQL", "🔍 Tavily Search", "✈️ AviationStack"]:
        st.markdown(f"<div class='sidebar-chip'>{tech}</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-title'>Agent Pipeline</div>", unsafe_allow_html=True)
    for step in ["⓪ Planner Agent ✦ NEW", "① Flight Agent", "② Hotel Agent", "③ Itinerary Agent", "④ Final Agent"]:
        st.markdown(f"<div class='sidebar-chip'>{step}</div>", unsafe_allow_html=True)

    # Show collected info if any
    if st.session_state.collected_info:
        st.markdown("<div class='sidebar-title'>📋 Collected Info</div>", unsafe_allow_html=True)
        info = st.session_state.collected_info
        pills_html = "<div class='info-pills'>"
        for key, label in [("source","From"), ("destination","To"), ("budget","Budget"), ("days","Days")]:
            val = info.get(key)
            if val:
                pills_html += f"<div class='info-pill'>✅ {label}: {val}</div>"
            else:
                pills_html += f"<div class='info-pill' style='border-color:#5c2020;color:#e07070;'>❓ {label}</div>"
        pills_html += "</div>"
        st.markdown(pills_html, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 New Trip", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.planning_complete = False
        st.session_state.collected_info = {}
        st.session_state.final_result = None
        # Generate a new hidden trip ID so LangGraph starts a fresh plan for this user
        st.session_state.trip_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
        st.rerun()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
    <img class="hero-bg"
         src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1400&q=80"
         alt="airplane above clouds"/>
    <div class="hero-content">
        <div class="hero-badge">✦ Multi-Agent AI System · Human-in-the-Loop</div>
        <div class="hero-title">✈️ AI Travel Booking System</div>
        <div class="hero-sub">A smart Planner Agent gathers your trip details first — then five specialized agents build your perfect travel plan.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Destination image strip ───────────────────────────────────────────────────
DESTINATIONS = [
    ("🇯🇵 Tokyo",     "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=300&q=70"),
    ("🇫🇷 Paris",     "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=300&q=70"),
    ("🇹🇭 Bangkok",   "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=300&q=70"),
    ("🇮🇹 Rome",      "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=300&q=70"),
    ("🇦🇪 Dubai",     "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=300&q=70"),
]

cols = st.columns(5)
for col, (name, img_url) in zip(cols, DESTINATIONS):
    with col:
        st.markdown(f"""
        <div style="border-radius:10px;overflow:hidden;position:relative;height:90px;cursor:pointer;">
            <img src="{img_url}" style="width:100%;height:100%;object-fit:cover;filter:brightness(0.55);" />
            <div style="position:absolute;bottom:8px;left:0;right:0;text-align:center;
                        color:#fff;font-size:0.8rem;font-weight:600;">{name}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Chat History Display ───────────────────────────────────────────────────────
if st.session_state.chat_history:
    st.markdown("<div class='sec-head'><span>💬 Conversation</span></div>", unsafe_allow_html=True)

    chat_html = "<div class='chat-container'>"
    for msg in st.session_state.chat_history:
        role = msg["role"]
        content = msg["content"].replace("\n", "<br>")
        if role == "user":
            chat_html += f"""
            <div class='chat-bubble user'>
                <div class='bubble-avatar user'>👤</div>
                <div class='bubble-text user'>{content}</div>
            </div>"""
        else:
            chat_html += f"""
            <div class='chat-bubble agent'>
                <div class='bubble-avatar agent'>🤖</div>
                <div class='bubble-text agent'>{content}</div>
            </div>"""
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

# ── Planner Status Banner ──────────────────────────────────────────────────────
if not st.session_state.planning_complete and st.session_state.chat_history:
    info = st.session_state.collected_info
    missing = [f for f in ["source", "destination", "budget", "days"] if not info.get(f)]
    if missing:
        st.markdown(
            f"<div class='planner-collecting'>⏳ <strong>Planner Agent</strong> is collecting required details — still need: "
            f"{', '.join(missing)}</div>",
            unsafe_allow_html=True
        )
elif st.session_state.planning_complete:
    st.markdown(
        "<div class='planner-ready'>✅ <strong>Planner Agent</strong> has all details — full pipeline executed!</div>",
        unsafe_allow_html=True
    )

# ── Input Area ────────────────────────────────────────────────────────────────
if not st.session_state.planning_complete:
    # Show quick-start chips only before first message
    if not st.session_state.chat_history:
        st.markdown("<div class='input-label'>🗺️ Describe your trip or answer the planner's questions</div>",
                    unsafe_allow_html=True)
        QUICK = ["7-day Japan under ₹2L", "Paris trip for 5 days", "Dubai weekend trip", "Bali backpacking 10 days"]
        qcols = st.columns(len(QUICK))
        quick_fill = st.session_state.get("quick_fill", "")
        for qc, label in zip(qcols, QUICK):
            with qc:
                if st.button(label, key=f"q_{label}"):
                    st.session_state["quick_fill"] = label
                    st.rerun()
        placeholder_text = "e.g. I want to go to Japan from Mumbai for 7 days with ₹2 lakhs budget"
    else:
        st.markdown("<div class='input-label'>💬 Reply to the Planner Agent</div>", unsafe_allow_html=True)
        placeholder_text = "Type your answer here..."

    user_input = st.text_area(
        "",
        value=st.session_state.get("quick_fill", ""),
        placeholder=placeholder_text,
        height=90,
        label_visibility="collapsed",
        key="user_input_box",
    )

    send_col, _ = st.columns([1, 3])
    with send_col:
        send_btn = st.button(
            "📤  Send" if st.session_state.chat_history else "🚀  Plan My Trip",
            use_container_width=True
        )

    if send_btn:
        if not user_input.strip():
            st.warning("Please type a message first.")
        else:
            user_text = user_input.strip()
            st.session_state["quick_fill"] = ""

            # Append to visual chat history
            st.session_state.chat_history.append({"role": "user", "content": user_text})

            # Use the combined username and hidden trip_id as the unique LangGraph thread
            actual_thread_id = f"{st.session_state.username}_{st.session_state.trip_id}"
            config = {"configurable": {"thread_id": actual_thread_id}}

            # Invoke the graph — it will resume from checkpoint with full history
            with st.spinner("🧠 Planner Agent is thinking..."):
                result = app.invoke(
                    {
                        "messages": [HumanMessage(content=user_text)],
                        "user_query": "",
                        "flight_results": "",
                        "hotel_results": "",
                        "itinerary": "",
                        "llm_calls": 0,
                        "source": None,
                        "destination": None,
                        "budget": None,
                        "days": None,
                        "ready_to_proceed": False,
                    },
                    config=config
                )

            # Update collected info from state
            st.session_state.collected_info = {
                "source":      result.get("source"),
                "destination": result.get("destination"),
                "budget":      result.get("budget"),
                "days":        result.get("days"),
            }

            ready = result.get("ready_to_proceed", False)

            if not ready:
                # Planner asked a follow-up question — grab the last AIMessage
                ai_msgs = [m for m in result["messages"] if isinstance(m, AIMessage)]
                if ai_msgs:
                    planner_reply = ai_msgs[-1].content
                    st.session_state.chat_history.append({"role": "agent", "content": planner_reply})
                st.rerun()

            else:
                # All fields collected — pipeline ran to completion
                st.session_state.planning_complete = True
                st.session_state.final_result = result

                # Add a confirmation message
                st.session_state.chat_history.append({
                    "role": "agent",
                    "content": (
                        f"✅ All details collected!\n\n"
                        f"📍 **From:** {result.get('source')}\n"
                        f"📍 **To:** {result.get('destination')}\n"
                        f"💰 **Budget:** {result.get('budget')}\n"
                        f"📅 **Days:** {result.get('days')}\n\n"
                        "Running the full agent pipeline now... scroll down to see results!"
                    )
                })
                st.rerun()

# ── Full Pipeline Results (shown after planning_complete) ──────────────────────
if st.session_state.planning_complete and st.session_state.final_result:
    result = st.session_state.final_result

    AGENT_META = {
        "planner_agent":   ("🧭", "Planner Agent"),
        "flight_agent":    ("✈️", "Flight Agent"),
        "hotel_agent":     ("🏨", "Hotel Agent"),
        "itinerary_agent": ("🗓️", "Itinerary Agent"),
        "final_agent":     ("🧠", "Final Agent"),
    }

    st.markdown("---")
    st.markdown("<div class='sec-head'><span>🤖 Agent Pipeline Results</span></div>", unsafe_allow_html=True)

    # Flight results
    with st.status("✈️  Flight Agent", state="complete", expanded=True):
        st.markdown(result.get("flight_results") or "_No flight data returned._")

    # Hotel results
    with st.status("🏨  Hotel Agent", state="complete", expanded=True):
        st.markdown(result.get("hotel_results") or "_No hotel data returned._")

    # Itinerary
    with st.status("🗓️  Itinerary Agent", state="complete", expanded=True):
        st.markdown(result.get("itinerary") or "_No itinerary generated._")

    # Final response — grab last AIMessage
    final_text = ""
    ai_msgs = [m for m in result["messages"] if isinstance(m, AIMessage)]
    if ai_msgs:
        final_text = ai_msgs[-1].content

    with st.status("🧠  Final Agent", state="complete", expanded=True):
        st.markdown(final_text or "_No final response._")

    # Metrics
    llm_calls = result.get("llm_calls", 0)
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="metric-val">5</div><div class="metric-lbl">Agents Run</div></div>
        <div class="metric-box"><div class="metric-val">{llm_calls}</div><div class="metric-lbl">LLM Calls</div></div>
        <div class="metric-box"><div class="metric-val">✅</div><div class="metric-lbl">Status</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Final plan card
    if final_text:
        st.markdown("<div class='sec-head'><span>🧠 Final Travel Plan</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='final-card'>{final_text}</div>", unsafe_allow_html=True)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"travel_plan_{timestamp}.md"
    save_dir = os.path.join(os.path.dirname(__file__), "travel_plans")
    os.makedirs(save_dir, exist_ok=True)

    user_query = result.get("user_query", "")
    file_content = f"""# Travel Plan
**Query:** {user_query}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User ID:** {st.session_state.username} (Trip ID: {st.session_state.trip_id})

---

## Trip Details
- **From:** {result.get('source', 'N/A')}
- **To:** {result.get('destination', 'N/A')}
- **Budget:** {result.get('budget', 'N/A')}
- **Days:** {result.get('days', 'N/A')}

---

## ✈️ Flight Information
{result.get('flight_results') or 'N/A'}

---

## 🏨 Hotel Information
{result.get('hotel_results') or 'N/A'}

---

## 🗓️ Itinerary
{result.get('itinerary') or 'N/A'}

---

## 🧠 Final Travel Plan
{final_text or 'N/A'}

---
*LLM Calls: {llm_calls}*
"""
    with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
        f.write(file_content)

    dl_col, info_col = st.columns([1, 3])
    with dl_col:
        st.download_button("⬇️ Download Plan", data=file_content,
                           file_name=filename, mime="text/markdown",
                           use_container_width=True)
    with info_col:
        st.markdown(f"<div class='save-bar'>📁 Auto-saved → <code>travel_plans/{filename}</code></div>",
                    unsafe_allow_html=True)
