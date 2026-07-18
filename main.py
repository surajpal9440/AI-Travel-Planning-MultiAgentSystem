'''
# pip install langgraph langchain langchain-openai langchain-groq langchain-community langchain-tavily psycopg[binary] psycopg_pool python-dotenv tavily-python pip install requests streamlit

# install PostgresSql and create database
CREATE DATABASE langgraph_memory;  ( or open pgadmin4 and create database there )
'''
# LangGraph Multi-Agent Travel Booking System with Long-Term Memory

# main.py

import os
from typing import TypedDict, Annotated, Optional
import operator
import re

import psycopg
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq

from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)

# ── State ──────────────────────────────────────────────────────────────────────
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int
    # New fields for the planner agent
    source: Optional[str]
    destination: Optional[str]
    budget: Optional[str]
    days: Optional[str]
    ready_to_proceed: bool


# ── Regex-based travel detail extractor ─────────────────────────────────
def _regex_extract(text: str) -> dict:
    """
    Deterministic extraction of travel fields using regex.
    Uses re.finditer for destination/source so false-positive "to"/"from"
    matches (like "want to plan") are skipped and the real value is found.
    """
    tl = text.lower()
    result = {"source": None, "destination": None, "budget": None, "days": None}

    # ─ Days ────────────────────────────────────────────────────────
    for pat in [
        r'(?:total\s+)?days?\s*[:\-]?\s*(\d+)',   # "total days: 15", "days 15"
        r'(\d+)\s*[\-]?\s*days?(?:\s+trip)?',      # "15-day trip", "15 days"
        r'for\s+(\d+)\s+days?',                     # "for 15 days"
        r'(\d+)\s+nights?',                         # "15 nights"
        r'(\d+)\s+weeks?',                          # "2 weeks" -> 14 days
    ]:
        m = re.search(pat, tl)
        if m:
            val = int(m.group(1))
            if 'week' in pat:
                val *= 7
            result["days"] = str(val)
            break

    # ─ Budget ───────────────────────────────────────────────────
    budget_pats = [
        (r'(\d+(?:\.\d+)?)\s*lakh[s]?',       lambda m, _t: f"{m.group(1)} lakh"),
        (r'(\d+(?:\.\d+)?)\s*crore[s]?',      lambda m, _t: f"{m.group(1)} crore"),
        (r'(?:rs\.?|inr|rupees?)\s*([\d,]+)', lambda m, _t: f"₹{m.group(1)}"),
        (r'₹\s*([\d,]+)',                      lambda m, _t: f"₹{m.group(1)}"),
        (r'\$\s*([\d,]+)',                     lambda m, _t: f"${m.group(1)}"),
        (r'budget\s+(?:of\s+|:)?([\d,]+)',    lambda m, _t: f"₹{m.group(1)}"),
    ]
    for pat, fmt in budget_pats:
        m = re.search(pat, tl)
        if m:
            result["budget"] = fmt(m, tl)
            break

    # ─ Destination – use finditer to skip false-positive "to" words ──
    # e.g. "i want TO plan" → skip; "from pune TO japan" → use "japan"
    DST_STOP = {
        'the', 'a', 'an', 'my', 'your', 'our', 'plan', 'book', 'go', 'be',
        'do', 'make', 'get', 'want', 'have', 'see', 'know', 'find', 'help',
        'provide', 'start', 'travel', 'fly', 'take', 'use', 'give', 'visit',
    }
    dst_patterns = [
        # Strong signals first (specific verb before "to")
        r'(?:trip\s+to|travel\s+to|going\s+to|fly(?:ing)?\s+to|visit(?:ing)?)\s+'
        r'([a-z][a-z ]{1,30}?)(?:\s+from\b|\s+with\b|\s+for\b|\s+in\s+\d|\.|,|$)',
        # Weaker: bare "to X" – iterate all matches to skip stop-words
        r'\bto\s+([a-z][a-z ]{1,25}?)(?:\s+from\b|\s+with\b|\s+for\b|\.|,|$)',
    ]
    for pat in dst_patterns:
        for m in re.finditer(pat, tl):   # ← KEY FIX: try every "to X" match
            raw = m.group(1).strip()
            first_word = raw.split()[0] if raw.split() else ""
            if first_word and first_word not in DST_STOP and raw not in DST_STOP:
                result["destination"] = raw.title()
                break
        if result["destination"]:
            break

    # ─ Source – use finditer to skip generic "from" phrases ───────────
    SRC_STOP = {'the', 'a', 'an', 'my', 'your', 'our', 'here', 'there'}
    for pat in [
        r'(?:departing|starting\s+from|flying\s+from|from)\s+'
        r'([a-z][a-z ,]{2,35}?)(?:\s+to\b|\s+for\b|\s+with\b|,|$)',
    ]:
        for m in re.finditer(pat, tl):   # ← iterate all "from X" matches
            raw = m.group(1).strip().rstrip(',')
            first_word = raw.split()[0] if raw.split() else ""
            if first_word and first_word not in SRC_STOP and raw not in SRC_STOP:
                result["source"] = raw.title()
                break
        if result["source"]:
            break

    return result


def _llm_extract_missing(field: str, conversation_text: str) -> Optional[str]:
    """
    Ask the LLM to extract ONE specific missing field.
    Uses a very direct, single-answer prompt to avoid conversational responses.
    """
    prompts = {
        "source": (
            f"In this travel conversation, what city or place is the traveler DEPARTING FROM?\n"
            f"Answer with ONLY the place name. If not stated, answer: NOT_FOUND\n\n"
            f"Conversation: {conversation_text}"
        ),
        "destination": (
            f"In this travel conversation, what city or country does the traveler want to GO TO?\n"
            f"Answer with ONLY the place name. If not stated, answer: NOT_FOUND\n\n"
            f"Conversation: {conversation_text}"
        ),
        "budget": (
            f"In this travel conversation, what is the travel BUDGET?\n"
            f"Accept Indian format: '1 lakh', '50000', '2 crore'. Also accept '$500', '₹1,00,000'.\n"
            f"Answer with ONLY the budget value. If not stated, answer: NOT_FOUND\n\n"
            f"Conversation: {conversation_text}"
        ),
        "days": (
            f"In this travel conversation, how many DAYS is the trip?\n"
            f"Answer with ONLY the number. If not stated, answer: NOT_FOUND\n\n"
            f"Conversation: {conversation_text}"
        ),
    }
    try:
        resp = llm.invoke([HumanMessage(content=prompts[field])]).content.strip().strip("\"'")
        if resp and "NOT_FOUND" not in resp.upper() and len(resp) < 80:
            return resp
    except Exception:
        pass
    return None


FIELD_LABELS = {
    "source":      "your departure city (where you'll travel FROM)",
    "destination": "your destination (where you want to GO)",
    "budget":      "your total budget (e.g. ₹1 lakh, $500)",
    "days":        "number of days for the trip",
}


def planner_agent(state: TravelState):
    """
    Extracts travel fields using regex first, then LLM for any gaps.
    Asks the user for any remaining missing fields (Human-in-the-Loop).
    """
    # Collect all human messages into one text block for extraction
    human_texts = [
        m.content for m in state["messages"]
        if isinstance(m, HumanMessage)
    ]
    full_text = "\n".join(human_texts)

    # Step 1: regex extraction (fast, deterministic)
    extracted = _regex_extract(full_text)

    # Step 2: for any field still None, try LLM extraction
    llm_call_count = 0
    for field in ("source", "destination", "budget", "days"):
        if extracted[field] is None:
            val = _llm_extract_missing(field, full_text)
            if val:
                extracted[field] = val
            llm_call_count += 1

    source      = extracted["source"]
    destination = extracted["destination"]
    budget      = extracted["budget"]
    days        = extracted["days"]
    ready       = all([source, destination, budget, days])

    new_messages = []
    user_query = state.get("user_query", "")

    if ready:
        user_query = (
            f"Plan a {days}-day trip from {source} to {destination} "
            f"with a budget of {budget}."
        )
    else:
        missing = [f for f, v in [
            ("source", source), ("destination", destination),
            ("budget", budget), ("days", days)
        ] if not v]
        missing_labels = [FIELD_LABELS[f] for f in missing]
        if len(missing_labels) == 1:
            question = f"Almost there! Could you please tell me {missing_labels[0]}?"
        else:
            items = "\n".join(f"  • {lbl}" for lbl in missing_labels)
            question = f"To complete your trip plan, I still need:\n{items}"
        new_messages = [AIMessage(content=question)]

    return {
        "source": source,
        "destination": destination,
        "budget": budget,
        "days": days,
        "ready_to_proceed": ready,
        "user_query": user_query,
        "messages": new_messages,
        "llm_calls": state.get("llm_calls", 0) + llm_call_count,
    }


# ── Conditional edge from planner ──────────────────────────────────────────────
def should_proceed(state: TravelState) -> str:
    """Route to flight_agent if all info is collected, else end (return to user)."""
    if state.get("ready_to_proceed"):
        return "flight_agent"
    return END


# ── Flight Agent ───────────────────────────────────────────────────────────────
def flight_agent(state: TravelState):
    query = state["user_query"]
    flight_data = search_flights(query)
    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content=f"Flight results fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# ── Hotel Agent ────────────────────────────────────────────────────────────────
def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = tavily_search(query)

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# ── Itinerary Agent ────────────────────────────────────────────────────────────
def itinerary_agent(state: TravelState):

    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}
    """

    response = llm.invoke([
        SystemMessage(
            content="You are an expert travel planner"
        ),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# ── Final Response Agent ───────────────────────────────────────────────────────
def final_agent(state: TravelState):

    final_prompt = f"""
    Generate final travel response.

    Flights:
    {state['flight_results']}

    Hotels:
    {state['hotel_results']}

    Itinerary:
    {state['itinerary']}
    """

    response = llm.invoke([
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# ── Build Graph ────────────────────────────────────────────────────────────────
graph = StateGraph(TravelState)

graph.add_node("planner_agent",   planner_agent)
graph.add_node("flight_agent",    flight_agent)
graph.add_node("hotel_agent",     hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent",     final_agent)

graph.add_edge(START, "planner_agent")

# Conditional routing: planner either ends (asks user) or proceeds to flights
graph.add_conditional_edges(
    "planner_agent",
    should_proceed,
    {
        "flight_agent": "flight_agent",
        END: END,
    }
)

graph.add_edge("flight_agent",    "hotel_agent")
graph.add_edge("hotel_agent",     "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent",     END)


# ── Persistent connection ──────────────────────────────────────────────────────
_conn = psycopg.connect(DATABASE_URL, autocommit=True)
checkpointer = PostgresSaver(_conn)
checkpointer.setup()

app = graph.compile(checkpointer=checkpointer)


# ── CLI entry-point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    config = {
        "configurable": {
            "thread_id": "user_aarohi"
        }
    }

    print("AI Travel Planner (type 'quit' to exit)\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        result = app.invoke(
            {
                "messages": [HumanMessage(content=user_input)],
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

        # Print the last AI message
        ai_msgs = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if ai_msgs:
            print(f"\nAgent: {ai_msgs[-1].content}\n")

        if result.get("ready_to_proceed"):
            print("\n✅ All details collected — plan generated above!")
            break
