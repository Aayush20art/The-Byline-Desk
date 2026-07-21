import os
import time
from typing import TypedDict, Annotated, List, Dict

import streamlit as st
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch

# ======================================================================
# PAGE CONFIG
# ======================================================================
st.set_page_config(
    page_title="The Byline Desk",
    page_icon="🖋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================================================================
# SECRETS -> ENV  (works locally via .env, and on Streamlit Cloud via
# the Secrets panel — just add MISTRAL_API_KEY, GOOGLE_API_KEY and
# TAVILY_API_KEY there and this picks them up automatically)
# ======================================================================
for _key in ("MISTRAL_API_KEY", "GOOGLE_API_KEY", "TAVILY_API_KEY"):
    if _key in st.secrets:
        os.environ[_key] = st.secrets[_key]

MISSING_KEYS = [k for k in ("MISTRAL_API_KEY", "GOOGLE_API_KEY", "TAVILY_API_KEY") if not os.environ.get(k)]

# ======================================================================
# STYLE — "The Byline Desk": a newsroom copy-desk where an AI writer
# drafts and a stricter AI editor won't sign off until it's right.
# ======================================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@400;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500;600&family=Caveat:wght@600;700&display=swap" rel="stylesheet">

<style>
:root{
  --ink:        #04100A;
  --panel:      #0A1A13;
  --panel-line: #1E3A2A;
  --paper:      #F6F1E4;
  --paper-edge: #E7DEC8;
  --ink-text:   #221F1A;
  --neon:       #35F2A0;
  --neon-d:     #0E6B44;
  --approve:    #2FD1C4;
  --approve-d:  #103F3A;
  --reject:     #E6483D;
  --reject-d:   #4A130F;
  --muted:      #8FAFA0;
  --paper2:     #efe7d4;
}

html, body, [class*="css"]{
  font-family: 'Source Serif 4', Georgia, serif;
}

.stApp{
  background:
    radial-gradient(1100px 500px at 12% -10%, #0E3323 0%, transparent 60%),
    radial-gradient(900px 500px at 100% 0%, #0A2A1D 0%, transparent 55%),
    radial-gradient(800px 460px at 50% 105%, rgba(53,242,160,0.10) 0%, transparent 65%),
    var(--ink);
  background-size: 180% 180%, 180% 180%, 180% 180%, 100% 100%;
  animation: driftBg 26s ease-in-out infinite;
}
@keyframes driftBg{
  0%{   background-position: 12% -10%, 100% 0%, 50% 105%, 0 0; }
  50%{  background-position: 22% 6%,   88% 12%, 46% 92%,  0 0; }
  100%{ background-position: 12% -10%, 100% 0%, 50% 105%, 0 0; }
}

/* drifting ink motes across the whole page — pure ambience */
.stApp::before{
  content:'';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-image:
    radial-gradient(2px 2px at 20% 30%, rgba(53,242,160,0.55) 0, transparent 60%),
    radial-gradient(2px 2px at 75% 15%, rgba(53,242,160,0.4) 0, transparent 60%),
    radial-gradient(1.5px 1.5px at 60% 70%, rgba(107,255,192,0.35) 0, transparent 60%),
    radial-gradient(1.5px 1.5px at 90% 60%, rgba(107,255,192,0.3) 0, transparent 60%),
    radial-gradient(2px 2px at 35% 85%, rgba(53,242,160,0.35) 0, transparent 60%);
  background-repeat: no-repeat;
  animation: floatMotes 18s ease-in-out infinite;
}
@keyframes floatMotes{
  0%,100%{ transform: translateY(0px); }
  50%{ transform: translateY(-22px); }
}

/* ---------------- Sidebar: the desk drawer ---------------- */
section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #0B1912 0%, #060F0A 100%);
  border-right: 1px solid var(--panel-line);
}
section[data-testid="stSidebar"] * { color: #D8DBE3; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3{
  font-family: 'Zilla Slab', serif;
  letter-spacing: .02em;
}
section[data-testid="stSidebar"] label{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.72rem !important;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--muted) !important;
}
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stTextArea textarea{
  background: #071510;
  border: 1px solid var(--panel-line);
  color: #EFE9DA;
  font-family: 'Source Serif 4', serif;
  transition: border-color .25s ease, box-shadow .25s ease;
}
section[data-testid="stSidebar"] .stTextInput input:focus,
section[data-testid="stSidebar"] .stTextArea textarea:focus{
  border-color: var(--neon);
  box-shadow: 0 0 0 3px rgba(53,242,160,0.15);
}

/* ---------------- Buttons everywhere ---------------- */
.stButton > button{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.8rem;
  letter-spacing: .08em;
  text-transform: uppercase;
  background: var(--neon);
  color: #04140D;
  border: none;
  border-radius: 3px;
  padding: 0.6rem 1.1rem;
  font-weight: 600;
  transition: transform .18s cubic-bezier(.34,1.56,.64,1), box-shadow .25s ease, background .25s ease;
  box-shadow: 0 2px 0 #0E6B44, 0 6px 14px rgba(0,0,0,.45);
}
.stButton > button:hover{
  transform: translateY(-2px) scale(1.015);
  background: #6BFFC0;
  box-shadow: 0 4px 0 #0E6B44, 0 12px 22px rgba(0,0,0,.55);
}
.stButton > button:active{
  transform: translateY(1px) scale(.99);
  box-shadow: 0 1px 0 #0E6B44;
}

/* ---------------- Masthead ---------------- */
.masthead{
  position: relative;
  text-align:center;
  padding: 1.6rem 0 1.1rem 0;
  border-bottom: 3px double var(--neon);
  margin-bottom: 1.8rem;
  animation: fadeDown .7s ease both;
  overflow: hidden;
}
.masthead::after{
  content:'';
  position:absolute;
  top:0; bottom:0; left:-40%;
  width: 40%;
  background: linear-gradient(90deg, transparent, rgba(53,242,160,0.16), transparent);
  animation: shimmerSweep 6s ease-in-out infinite;
}
@keyframes shimmerSweep{
  0%{ left:-40%; }
  55%{ left:110%; }
  100%{ left:110%; }
}
.masthead h1{
  font-family: 'Zilla Slab', serif;
  font-weight: 700;
  font-size: 3.1rem;
  color: #EAFBF3;
  letter-spacing: .01em;
  margin: 0;
  animation: glowPulse 5s ease-in-out infinite;
}
@keyframes glowPulse{
  0%,100%{ text-shadow: 0 0 0 rgba(243,236,218,0); }
  50%{ text-shadow: 0 0 18px rgba(243,236,218,0.28); }
}
.masthead .tagline{
  font-family: 'Source Serif 4', serif;
  font-style: italic;
  color: var(--muted);
  font-size: 1.02rem;
  margin-top: .3rem;
}
.masthead .tagline::after{
  content:'▍';
  display:inline-block;
  margin-left:.15rem;
  color: var(--neon);
  animation: blink 1.1s steps(1) infinite;
}
.masthead .meta{
  font-family: 'IBM Plex Mono', monospace;
  font-size: .7rem;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: var(--neon);
  margin-top: .7rem;
}
@keyframes fadeDown{
  from{ opacity:0; transform: translateY(-14px); }
  to{ opacity:1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce){
  .stApp, .stApp::before, .masthead::after, .masthead h1, .masthead .tagline::after,
  .empty-desk .glyph, .empty-desk, .stButton > button{ animation: none !important; }
}

/* ---------------- Status ticker while the graph runs ---------------- */
.desk-log{
  font-family:'IBM Plex Mono', monospace;
  font-size: .84rem;
  color:#D8DBE3;
  background: var(--panel);
  border: 1px solid var(--panel-line);
  border-left: 3px solid var(--neon);
  border-radius: 4px;
  padding: .9rem 1.1rem;
  margin-bottom: .5rem;
  animation: fadeIn .35s ease both;
}
.desk-log .cursor::after{
  content:'▍';
  animation: blink 1s steps(1) infinite;
  color: var(--neon);
}
@keyframes blink{ 50%{ opacity:0; } }
@keyframes fadeIn{ from{opacity:0; transform: translateY(6px);} to{opacity:1; transform:translateY(0);} }

/* ---------------- Revision chips ---------------- */
.chip-row{ display:flex; gap:.5rem; margin: 0 0 1.1rem 0; flex-wrap:wrap; }
.chip{
  font-family:'IBM Plex Mono', monospace;
  font-size:.72rem;
  letter-spacing:.08em;
  padding:.32rem .7rem;
  border-radius: 999px;
  border:1px solid var(--panel-line);
  color: var(--muted);
  background: var(--panel);
  transition: all .2s ease;
}
.chip.approved{ border-color: var(--approve); color:#BFF0D6; background: rgba(62,139,99,.12); }
.chip.rejected{ border-color: var(--reject); color:#F3C7C2; background: rgba(193,68,58,.12); }

/* ---------------- Manuscript card ---------------- */
.manuscript-wrap{
  position: relative;
  margin-bottom: 2.6rem;
  animation: riseIn .5s cubic-bezier(.2,.8,.2,1) both;
}
@keyframes riseIn{
  from{ opacity:0; transform: translateY(18px) rotate(0deg); }
  to{ opacity:1; transform: translateY(0) rotate(var(--tilt,0deg)); }
}
.manuscript{
  --tilt: -0.6deg;
  background: linear-gradient(180deg, var(--paper) 0%, var(--paper2) 100%);
  color: var(--ink-text);
  border-radius: 2px;
  padding: 1.9rem 2.1rem 1.6rem 2.1rem;
  box-shadow: 0 1px 0 var(--paper-edge), 0 18px 34px rgba(0,0,0,.45), 0 2px 6px rgba(0,0,0,.25);
  transform: rotate(var(--tilt));
  transition: transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s ease;
  position: relative;
  overflow: hidden;
}
.manuscript::before{
  content:'';
  position:absolute; inset:0;
  background: repeating-linear-gradient(0deg, rgba(0,0,0,0.018) 0px, rgba(0,0,0,0.018) 1px, transparent 1px, transparent 28px);
  pointer-events:none;
}
.manuscript:hover{
  transform: rotate(0deg) translateY(-6px) scale(1.008);
  box-shadow: 0 1px 0 var(--paper-edge), 0 28px 46px rgba(0,0,0,.55), 0 4px 10px rgba(0,0,0,.3);
}
.manuscript .label{
  font-family:'IBM Plex Mono', monospace;
  font-size:.68rem;
  letter-spacing:.16em;
  text-transform:uppercase;
  color:#8a7f5f;
  margin-bottom:.5rem;
}
.manuscript h3{
  font-family:'Zilla Slab', serif;
  font-size:1.25rem;
  margin: 0 0 .8rem 0;
  color: var(--ink-text);
  border-bottom: 1px solid var(--paper-edge);
  padding-bottom:.5rem;
}
.manuscript .body-text{
  font-family:'Source Serif 4', serif;
  font-size:1.02rem;
  line-height:1.65;
  white-space: pre-wrap;
}

/* Stamp */
.stamp{
  position:absolute;
  top: 1.3rem; right: 1.6rem;
  font-family:'IBM Plex Mono', monospace;
  font-weight:700;
  font-size:1.05rem;
  letter-spacing:.12em;
  padding:.4rem .8rem;
  border: 3px solid currentColor;
  border-radius: 6px;
  text-transform:uppercase;
  transform: rotate(-11deg) scale(2.4);
  opacity:0;
  animation: stampSlam .55s cubic-bezier(.2,1.4,.4,1) .15s forwards;
  mix-blend-mode: multiply;
}
.stamp.approved{ color: var(--approve-d); }
.stamp.rejected{ color: var(--reject-d); }
@keyframes stampSlam{
  0%{ opacity:0; transform: rotate(-11deg) scale(2.6); }
  60%{ opacity:1; transform: rotate(-11deg) scale(.92); }
  80%{ transform: rotate(-11deg) scale(1.06); }
  100%{ opacity:1; transform: rotate(-11deg) scale(1); }
}

/* Red-pen margin note */
.redpen{
  font-family: 'Caveat', cursive;
  color: #9c2b22;
  font-size: 1.28rem;
  line-height: 1.35;
  margin-top: 1rem;
  padding-top: .8rem;
  border-top: 1px dashed #c98f88;
  transform: rotate(-0.4deg);
}
.redpen .tag{
  font-family:'IBM Plex Mono', monospace;
  font-size:.66rem;
  letter-spacing:.1em;
  color:#9c2b22;
  text-transform:uppercase;
  display:block;
  margin-bottom:.25rem;
}

/* Final approved banner */
.final-banner{
  background: linear-gradient(135deg, var(--approve-d), #123326);
  border: 1px solid var(--approve);
  border-radius: 6px;
  padding: 1.1rem 1.4rem;
  margin-bottom: 1.4rem;
  display:flex; align-items:center; gap:.8rem;
  animation: fadeIn .4s ease both;
}
.final-banner .icon{ font-size:1.6rem; }
.final-banner .txt{ font-family:'IBM Plex Mono', monospace; color:#D9F2E4; font-size:.85rem; letter-spacing:.04em; }

.copy-btn{
  font-family:'IBM Plex Mono', monospace;
  font-size:.72rem;
  letter-spacing:.08em;
  text-transform:uppercase;
  background: transparent;
  color: var(--neon);
  border: 1px solid var(--neon);
  border-radius: 4px;
  padding: .4rem .8rem;
  cursor:pointer;
  transition: all .2s ease;
}
.copy-btn:hover{ background: var(--neon); color:#04140D; transform: translateY(-1px); }

/* Empty state — the homepage moment */
.empty-desk{
  position: relative;
  text-align:center;
  padding: 4.2rem 1rem 3.6rem 1rem;
  color: var(--muted);
  border: 1px dashed var(--panel-line);
  border-radius: 10px;
  animation: fadeIn .6s ease both, borderGlow 4s ease-in-out infinite;
  overflow: hidden;
}
.empty-desk::before{
  content:'';
  position:absolute; inset:0;
  background: radial-gradient(420px 220px at 50% 0%, rgba(53,242,160,0.08), transparent 70%);
  animation: floatMotes 9s ease-in-out infinite;
  pointer-events:none;
}
@keyframes borderGlow{
  0%,100%{ border-color: var(--panel-line); box-shadow: 0 0 0 rgba(53,242,160,0); }
  50%{ border-color: rgba(53,242,160,0.55); box-shadow: 0 0 30px rgba(53,242,160,0.08) inset; }
}
.empty-desk .glyph{
  font-size:3rem;
  margin-bottom:.8rem;
  opacity:.85;
  display:inline-block;
  animation: bob 3.2s ease-in-out infinite;
}
@keyframes bob{
  0%,100%{ transform: translateY(0) rotate(-2deg); }
  50%{ transform: translateY(-12px) rotate(2deg); }
}
.empty-desk h4{
  font-family:'Zilla Slab', serif;
  color:#D8DBE3;
  font-size: 1.5rem;
  margin: 0 0 .4rem 0;
  letter-spacing:.01em;
}
.empty-desk .sub{
  font-family:'Source Serif 4', serif;
  font-style: italic;
  font-size: 1rem;
  position: relative;
  z-index:1;
}
.empty-desk .hint{
  display:inline-block;
  margin-top:1.2rem;
  font-family:'IBM Plex Mono', monospace;
  font-size:.68rem;
  letter-spacing:.14em;
  text-transform:uppercase;
  color: var(--neon);
  opacity:.85;
  position: relative;
  z-index:1;
  animation: hintPulse 2.4s ease-in-out infinite;
}
@keyframes hintPulse{
  0%,100%{ opacity:.5; }
  50%{ opacity:1; }
}

/* idle glow ring on the primary CTA so the empty page still feels alive */
.stButton > button{ position: relative; }
.stButton > button::after{
  content:'';
  position:absolute; inset:-3px;
  border-radius: 5px;
  border: 1px solid rgba(53,242,160,0.5);
  opacity:0;
  animation: ctaPulse 2.6s ease-out infinite;
  pointer-events:none;
}
@keyframes ctaPulse{
  0%{ opacity:.55; transform: scale(1); }
  100%{ opacity:0; transform: scale(1.12); }
}

/* Key warning */
.key-warning{
  font-family:'IBM Plex Mono', monospace;
  font-size:.78rem;
  color:#F3C7C2;
  background: rgba(193,68,58,.12);
  border:1px solid var(--reject);
  border-radius:4px;
  padding:.7rem 1rem;
  margin-bottom:1rem;
}
</style>
""", unsafe_allow_html=True)

# ======================================================================
# GRAPH DEFINITION  (unchanged logic from the source pipeline)
# ======================================================================

class State(TypedDict):
    topic: str
    messages: Annotated[list, add_messages]
    draft: str
    review_feedback: str
    is_approved: bool
    attempt: int
    max_attempts: int


WRITER_SYSTEM_PROMPT = (
    "You are an expert LinkedIn content writer. Your job is to write "
    "engaging, professional LinkedIn posts about the given topic. "
    "If the topic requires up-to-date information, statistics, or "
    "current trends, use the web search tool to gather fresh context "
    "before writing. If you have already received feedback on a "
    "previous draft, carefully address every point in the new draft. "
    "Rules for good LinkedIn posts: strong hook in the first line, "
    "1 clear takeaway, easy to skim (short paragraphs), around "
    "150-200 words, ends with a question or call-to-action to invite "
    "engagement. Do not use hashtags."
)

REVIEWER_SYSTEM_PROMPT = (
    "You are a strict LinkedIn content reviewer. You judge whether a "
    "post is publish-ready. Evaluate against these criteria:\n"
    "1. Strong hook in the first line\n"
    "2. One clear, valuable takeaway\n"
    "3. Easy to skim — uses short paragraphs\n"
    "4. Roughly 150-200 words\n"
    "5. Ends with an engaging question or CTA\n"
    "6. Professional but human tone (not corporate-robotic)\n"
    "7. No hashtags\n\n"
    "Respond in exactly this format:\n"
    "VERDICT: APPROVED or REJECTED\n"
    "FEEDBACK: <one short paragraph explaining why>\n\n"
    "Be strict but fair. Approve only if the post genuinely meets all "
    "criteria. Reject if even one criterion is clearly missing."
)


@st.cache_resource(show_spinner=False)
def build_graph():
    search_tool = TavilySearch(max_results=3)
    tools = [search_tool]

    writer_llm = ChatMistralAI(model="mistral-small-2506", temperature=0.7)
    writer_llm_with_tools = writer_llm.bind_tools(tools)

    reviewer_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

    def writer_node(state: State) -> dict:
        attempt = state.get("attempt", 0) + 1
        topic = state["topic"]
        previous_feedback = state["review_feedback"]

        if attempt == 1:
            user_message = (
                f"Write a LinkedIn post on this topic {topic}"
                f"if you need current info search the web first "
            )
        else:
            user_message = (
                f"your previous draft on '{topic}' was rejected"
                f"Here is the reviewer's feedback \n\n {previous_feedback}\n\n"
                f"Write a new, improved draft that fixes every issue mentiond"
                f"do not repeat the same mistake"
            )
        messages = [("system", WRITER_SYSTEM_PROMPT), ("human", user_message)]
        response = writer_llm_with_tools.invoke(messages)

        return {"messages": [("human", user_message), response], "attempt": attempt}

    tool_node = ToolNode(tools)

    def extract_draft_node(state: State) -> dict:
        last_message = state["messages"][-1]
        return {"draft": last_message.content}

    def reviewer_node(state: State) -> dict:
        draft = state["draft"]
        prompt = f"review this LinkedIn post draft : \n{draft}\ngive your reviews"
        response = reviewer_llm.invoke([("system", REVIEWER_SYSTEM_PROMPT), ("human", prompt)])
        review_text = response.content.strip()

        is_approved = "APPROVED" in review_text.upper().split("FEEDBACK")[0]

        if "FEEDBACK:" in review_text:
            feedback = review_text.split("FEEDBACK:", 1)[1].strip()
        else:
            feedback = review_text

        return {"review_feedback": feedback, "is_approved": is_approved}

    def should_use_tool(state: State):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return "extract_draft"

    def should_stop_looping(state: State):
        if state["is_approved"]:
            return END
        if state["attempt"] >= state.get("max_attempts", 3):
            return END
        return "writer"

    graph = StateGraph(State)
    graph.add_node("writer", writer_node)
    graph.add_node("tools", tool_node)
    graph.add_node("extract_draft", extract_draft_node)
    graph.add_node("reviewer", reviewer_node)

    graph.add_edge(START, "writer")
    graph.add_conditional_edges("writer", should_use_tool)
    graph.add_edge("tools", "reviewer")
    graph.add_edge("extract_draft", "reviewer")
    graph.add_conditional_edges("reviewer", should_stop_looping)

    return graph.compile()


# ======================================================================
# SIDEBAR — the desk drawer
# ======================================================================
with st.sidebar:
    st.markdown("## 🖋️ The Byline Desk")
    st.caption("An AI writer drafts. A stricter AI editor won't sign off until it's right.")
    st.markdown("---")

    topic = st.text_area(
        "Topic for the post",
        placeholder="e.g. why most technical interviews test the wrong thing",
        height=100,
    )
    max_attempts = st.slider("Max revision rounds", min_value=1, max_value=5, value=3)

    st.markdown("---")
    st.markdown(
        "<span style='font-family:IBM Plex Mono; font-size:.7rem; letter-spacing:.1em; color:#7C8394;'>"
        "WRITER · mistral-small &nbsp;|&nbsp; EDITOR · gemini-2.5-flash</span>",
        unsafe_allow_html=True,
    )

    generate = st.button("Send to the desk →", use_container_width=True)

    if MISSING_KEYS:
        st.markdown(
            f"<div class='key-warning'>Missing: {', '.join(MISSING_KEYS)}<br>"
            f"Add these in Streamlit Cloud → App settings → Secrets.</div>",
            unsafe_allow_html=True,
        )

# ======================================================================
# MASTHEAD
# ======================================================================
st.markdown("""
<div class="masthead">
  <h1>THE BYLINE DESK</h1>
  <div class="tagline">"publish nothing the editor hasn't signed off on"</div>
  <div class="meta">Vol. I · Drafted by Mistral · Reviewed by Gemini · Sourced via Tavily</div>
</div>
""", unsafe_allow_html=True)

# ======================================================================
# SESSION STATE
# ======================================================================
if "records" not in st.session_state:
    st.session_state.records = []
if "final" not in st.session_state:
    st.session_state.final = None

# ======================================================================
# RUN
# ======================================================================
if generate:
    if not topic.strip():
        st.warning("Give the desk a topic first.")
    elif MISSING_KEYS:
        st.error("Can't run — API keys are missing. Check the sidebar.")
    else:
        graph_app = build_graph()
        st.session_state.records = []
        st.session_state.final = None

        log_box = st.empty()
        seen_attempts = set()

        def log(msg):
            log_box.markdown(f"<div class='desk-log'>{msg}<span class='cursor'></span></div>", unsafe_allow_html=True)

        initial_state = {
            "topic": topic,
            "messages": [],
            "draft": "",
            "review_feedback": "",
            "is_approved": False,
            "attempt": 0,
            "max_attempts": max_attempts,
        }

        log("&gt; opening a new file on the desk...")
        time.sleep(0.3)

        final_state = initial_state
        for state in graph_app.stream(initial_state, stream_mode="values"):
            final_state = state
            att = state.get("attempt", 0)
            draft = state.get("draft", "")
            feedback = state.get("review_feedback", "")
            approved = state.get("is_approved", False)

            if att and not draft:
                log(f"&gt; writer is drafting revision {att}...")
            elif att and draft and not feedback:
                log(f"&gt; revision {att} drafted — walking it over to the editor...")
            elif att and draft and feedback and att not in seen_attempts:
                seen_attempts.add(att)
                verdict = "APPROVED" if approved else "REJECTED"
                log(f"&gt; editor's verdict on revision {att}: <b>{verdict}</b>")
                st.session_state.records.append(
                    {"attempt": att, "draft": draft, "feedback": feedback, "approved": approved}
                )

        log_box.empty()
        st.session_state.final = final_state

# ======================================================================
# RESULTS
# ======================================================================
records: List[Dict] = st.session_state.records

if not records:
    st.markdown("""
    <div class="empty-desk">
      <div class="glyph">🗞️</div>
      <h4>The desk is empty</h4>
      <div class="sub">Waiting on tonight's story.</div>
      <div class="hint">Type a topic in the sidebar → Send to the desk</div>
    </div>
    """, unsafe_allow_html=True)
else:
    final = st.session_state.final or {}
    approved_final = final.get("is_approved", False)

    # Chip row of all revisions
    chips = ""
    for r in records:
        cls = "approved" if r["approved"] else "rejected"
        chips += f"<span class='chip {cls}'>REV {r['attempt']} · {'APPROVED' if r['approved'] else 'REJECTED'}</span>"
    st.markdown(f"<div class='chip-row'>{chips}</div>", unsafe_allow_html=True)

    if approved_final:
        st.markdown("""
        <div class="final-banner">
          <div class="icon">✅</div>
          <div class="txt">SIGNED OFF — this draft is publish-ready.</div>
        </div>
        """, unsafe_allow_html=True)
    elif records:
        st.markdown("""
        <div class="final-banner" style="background:linear-gradient(135deg,#5C221D,#33130F); border-color:var(--reject);">
          <div class="icon">⏳</div>
          <div class="txt" style="color:#F3D6D2;">MAX ROUNDS REACHED — editor still has notes. Best draft is below.</div>
        </div>
        """, unsafe_allow_html=True)

    # Manuscript cards, most recent first
    for r in reversed(records):
        tilt = -0.6 if r["attempt"] % 2 == 0 else 0.5
        stamp_cls = "approved" if r["approved"] else "rejected"
        stamp_txt = "Approved" if r["approved"] else "Rejected"

        redpen = ""
        if not r["approved"]:
            redpen = f"""<div class="redpen"><span class="tag">Editor's note</span>{r['feedback']}</div>"""

        st.markdown(f"""
        <div class="manuscript-wrap" style="--tilt:{tilt}deg;">
          <div class="manuscript" style="--tilt:{tilt}deg;">
            <div class="stamp {stamp_cls}">{stamp_txt}</div>
            <div class="label">Revision {r['attempt']} of {max_attempts}</div>
            <h3>{topic.strip() or 'Untitled draft'}</h3>
            <div class="body-text">{r['draft']}</div>
            {redpen}
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Copy button for the best/final draft — st.code() ships its own
    # reliable copy icon, so we don't hand-roll JS/HTML escaping.
    st.markdown("<div class='label' style='margin-bottom:.3rem;'>Latest draft — click the copy icon on hover</div>", unsafe_allow_html=True)
    st.code(records[-1]["draft"], language=None)
