import os
import time
from typing import TypedDict, Annotated, List, Dict

import streamlit as st
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_mistralai import ChatMistralAI
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
# the Secrets panel — just add MISTRAL_API_KEY and TAVILY_API_KEY there
# and this picks them up automatically)
# ======================================================================
for _key in ("MISTRAL_API_KEY", "TAVILY_API_KEY"):
    if _key in st.secrets:
        os.environ[_key] = st.secrets[_key]

MISSING_KEYS = [k for k in ("MISTRAL_API_KEY", "TAVILY_API_KEY") if not os.environ.get(k)]

# ======================================================================
# STYLE — "The Byline Desk": a newsroom copy-desk where an AI writer
# drafts and a stricter AI editor won't sign off until it's right.
# Fully responsive: phone (<576px), tablet (576-1024px), laptop (>1024px)
# ======================================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@400;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500;600&family=Caveat:wght@600;700&display=swap" rel="stylesheet">

<style>
:root{
  --ink:        #12151C;
  --panel:      #181C26;
  --panel-line: #2A2F3C;
  --paper:      #F6F1E4;
  --paper-edge: #E7DEC8;
  --ink-text:   #221F1A;
  --gold:       #C9A227;
  --approve:    #3E8B63;
  --approve-d:  #234A36;
  --reject:     #C1443A;
  --reject-d:   #5C221D;
  --muted:      #9AA1AE;
  --paper2:     #efe7d4;
}

html, body, [class*="css"]{
  font-family: 'Source Serif 4', Georgia, serif;
}

.stApp{
  background:
    radial-gradient(1100px 500px at 12% -10%, #1B2130 0%, transparent 60%),
    radial-gradient(900px 500px at 100% 0%, #1A2A24 0%, transparent 55%),
    var(--ink);
}

/* ---------------- Make Streamlit's own layout fluid ---------------- */
.block-container{
  padding-left: 3rem;
  padding-right: 3rem;
  padding-top: 2rem;
  max-width: 1100px;
  transition: padding .2s ease;
}
img, .manuscript, .desk-log, .final-banner, .empty-desk{
  max-width: 100%;
  box-sizing: border-box;
}

/* ---------------- Sidebar: the desk drawer ---------------- */
section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #14171F 0%, #10131A 100%);
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
  background: #0F1218;
  border: 1px solid var(--panel-line);
  color: #EFE9DA;
  font-family: 'Source Serif 4', serif;
  transition: border-color .25s ease, box-shadow .25s ease;
}
section[data-testid="stSidebar"] .stTextInput input:focus,
section[data-testid="stSidebar"] .stTextArea textarea:focus{
  border-color: var(--gold);
  box-shadow: 0 0 0 3px rgba(201,162,39,0.15);
}

/* ---------------- Buttons everywhere ---------------- */
.stButton > button{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.8rem;
  letter-spacing: .08em;
  text-transform: uppercase;
  background: var(--gold);
  color: #171208;
  border: none;
  border-radius: 3px;
  padding: 0.6rem 1.1rem;
  font-weight: 600;
  transition: transform .18s cubic-bezier(.34,1.56,.64,1), box-shadow .25s ease, background .25s ease;
  box-shadow: 0 2px 0 #8a6d16, 0 6px 14px rgba(0,0,0,.35);
  width: 100%;
}
.stButton > button:hover{
  transform: translateY(-2px) scale(1.015);
  background: #DDB338;
  box-shadow: 0 4px 0 #8a6d16, 0 12px 22px rgba(0,0,0,.45);
}
.stButton > button:active{
  transform: translateY(1px) scale(.99);
  box-shadow: 0 1px 0 #8a6d16;
}

/* ---------------- Masthead ---------------- */
.masthead{
  text-align:center;
  padding: 1.6rem 0 1.1rem 0;
  border-bottom: 3px double var(--gold);
  margin-bottom: 1.8rem;
  animation: fadeDown .7s ease both;
}
.masthead h1{
  font-family: 'Zilla Slab', serif;
  font-weight: 700;
  font-size: clamp(1.7rem, 5vw, 3.1rem);
  color: #F3ECDA;
  letter-spacing: .01em;
  margin: 0;
  line-height: 1.15;
}
.masthead .tagline{
  font-family: 'Source Serif 4', serif;
  font-style: italic;
  color: var(--muted);
  font-size: clamp(.82rem, 2.4vw, 1.02rem);
  margin-top: .3rem;
  padding: 0 .5rem;
}
.masthead .meta{
  font-family: 'IBM Plex Mono', monospace;
  font-size: clamp(.58rem, 1.6vw, .7rem);
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--gold);
  margin-top: .7rem;
  padding: 0 .5rem;
  word-break: break-word;
}
@keyframes fadeDown{
  from{ opacity:0; transform: translateY(-14px); }
  to{ opacity:1; transform: translateY(0); }
}

/* ---------------- Status ticker while the graph runs ---------------- */
.desk-log{
  font-family:'IBM Plex Mono', monospace;
  font-size: clamp(.74rem, 2vw, .84rem);
  color:#D8DBE3;
  background: var(--panel);
  border: 1px solid var(--panel-line);
  border-left: 3px solid var(--gold);
  border-radius: 4px;
  padding: .9rem 1.1rem;
  margin-bottom: .5rem;
  animation: fadeIn .35s ease both;
  word-wrap: break-word;
}
.desk-log .cursor::after{
  content:'▍';
  animation: blink 1s steps(1) infinite;
  color: var(--gold);
}
@keyframes blink{ 50%{ opacity:0; } }
@keyframes fadeIn{ from{opacity:0; transform: translateY(6px);} to{opacity:1; transform:translateY(0);} }

/* ---------------- Revision chips ---------------- */
.chip-row{ display:flex; gap:.5rem; margin: 0 0 1.1rem 0; flex-wrap:wrap; }
.chip{
  font-family:'IBM Plex Mono', monospace;
  font-size: clamp(.66rem, 1.8vw, .72rem);
  letter-spacing:.08em;
  padding:.32rem .7rem;
  border-radius: 999px;
  border:1px solid var(--panel-line);
  color: var(--muted);
  background: var(--panel);
  transition: all .2s ease;
  white-space: nowrap;
}
.chip.approved{ border-color: var(--approve); color:#BFF0D6; background: rgba(62,139,99,.12); }
.chip.rejected{ border-color: var(--reject); color:#F3C7C2; background: rgba(193,68,58,.12); }

/* ---------------- Manuscript card ---------------- */
.manuscript-wrap{
  position: relative;
  margin-bottom: 2.6rem;
  animation: riseIn .5s cubic-bezier(.2,.8,.2,1) both;
  width: 100%;
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
  padding: clamp(1.2rem, 3vw, 1.9rem) clamp(1.1rem, 3.5vw, 2.1rem) clamp(1.1rem, 2.5vw, 1.6rem);
  box-shadow: 0 1px 0 var(--paper-edge), 0 18px 34px rgba(0,0,0,.45), 0 2px 6px rgba(0,0,0,.25);
  transform: rotate(var(--tilt));
  transition: transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s ease;
  position: relative;
  overflow: hidden;
  width: 100%;
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
  font-size: clamp(1.05rem, 3vw, 1.25rem);
  margin: 0 0 .8rem 0;
  color: var(--ink-text);
  border-bottom: 1px solid var(--paper-edge);
  padding-bottom:.5rem;
  word-wrap: break-word;
}
.manuscript .body-text{
  font-family:'Source Serif 4', serif;
  font-size: clamp(.92rem, 2.4vw, 1.02rem);
  line-height:1.65;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Stamp */
.stamp{
  position:absolute;
  top: 1.3rem; right: 1.6rem;
  font-family:'IBM Plex Mono', monospace;
  font-weight:700;
  font-size: clamp(.82rem, 2.4vw, 1.05rem);
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
  font-size: clamp(1.05rem, 3vw, 1.28rem);
  line-height: 1.35;
  margin-top: 1rem;
  padding-top: .8rem;
  border-top: 1px dashed #c98f88;
  transform: rotate(-0.4deg);
  word-wrap: break-word;
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
  padding: 1rem 1.2rem;
  margin-bottom: 1.4rem;
  display:flex; align-items:center; gap:.8rem;
  animation: fadeIn .4s ease both;
  flex-wrap: wrap;
}
.final-banner .icon{ font-size: clamp(1.2rem, 3vw, 1.6rem); }
.final-banner .txt{ font-family:'IBM Plex Mono', monospace; color:#D9F2E4; font-size: clamp(.72rem, 2vw, .85rem); letter-spacing:.04em; }

.copy-btn{
  font-family:'IBM Plex Mono', monospace;
  font-size:.72rem;
  letter-spacing:.08em;
  text-transform:uppercase;
  background: transparent;
  color: var(--gold);
  border: 1px solid var(--gold);
  border-radius: 4px;
  padding: .55rem .8rem;
  cursor:pointer;
  transition: all .2s ease;
  width: 100%;
  max-width: 260px;
}
.copy-btn:hover{ background: var(--gold); color:#171208; transform: translateY(-1px); }

/* Empty state */
.empty-desk{
  text-align:center;
  padding: clamp(2rem, 6vw, 3.2rem) 1rem;
  color: var(--muted);
  border: 1px dashed var(--panel-line);
  border-radius: 8px;
  animation: fadeIn .5s ease both;
}
.empty-desk .glyph{ font-size: clamp(1.8rem, 5vw, 2.4rem); margin-bottom:.6rem; opacity:.7; }
.empty-desk h4{ font-family:'Zilla Slab', serif; color:#D8DBE3; margin: 0 0 .3rem 0; font-size: clamp(1rem, 3vw, 1.2rem); }

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
  word-wrap: break-word;
}

/* =====================================================================
   BREAKPOINTS
   Laptop/desktop  : > 1024px  (defaults above already target this)
   Tablet (iPad)   : 577px - 1024px
   Phone (iPhone)  : <= 576px
   ===================================================================== */

/* ---- Tablets (iPad portrait/landscape, small laptops) ---- */
@media (max-width: 1024px){
  .block-container{
    padding-left: 1.5rem;
    padding-right: 1.5rem;
    padding-top: 1.2rem;
  }
  .manuscript{ --tilt: 0deg !important; transform: none !important; }
  .manuscript:hover{ transform: translateY(-4px) !important; }
  .stamp{ top: 1rem; right: 1rem; transform: rotate(-8deg) scale(1.6); }
  @keyframes stampSlam{
    0%{ opacity:0; transform: rotate(-8deg) scale(1.8); }
    60%{ opacity:1; transform: rotate(-8deg) scale(.95); }
    100%{ opacity:1; transform: rotate(-8deg) scale(1); }
  }
}

/* ---- Phones (iPhone SE up to Pro Max, portrait & landscape) ---- */
@media (max-width: 576px){
  .block-container{
    padding-left: .9rem;
    padding-right: .9rem;
    padding-top: .8rem;
  }
  .masthead{ padding: 1.1rem 0 .8rem 0; margin-bottom: 1.2rem; }
  .chip-row{ gap:.35rem; }
  .chip{ padding:.28rem .55rem; }
  .manuscript{ --tilt: 0deg !important; transform:none !important; padding: 1.1rem 1rem; border-radius: 6px; }
  .manuscript:hover{ transform: none !important; }
  .stamp{
    position: static;
    display: inline-block;
    margin-bottom: .7rem;
    transform: rotate(-4deg) scale(1);
    animation: none;
    opacity: 1;
  }
  .manuscript h3{ padding-right: 0; }
  .final-banner{ padding: .85rem 1rem; gap:.6rem; }
  .copy-btn{ max-width: none; }
}

/* ---- Very narrow phones ---- */
@media (max-width: 380px){
  .masthead h1{ font-size: 1.5rem; letter-spacing: 0; }
  .manuscript{ padding: .9rem .8rem; }
}
</style>
""", unsafe_allow_html=True)

# ======================================================================
# GRAPH DEFINITION  (unchanged logic from the source pipeline, except
# both the writer and the reviewer now run on Mistral)
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

    # Writer: fast, creative drafting model
    writer_llm = ChatMistralAI(model="mistral-small-2506", temperature=0.7)
    writer_llm_with_tools = writer_llm.bind_tools(tools)

    # Reviewer: same provider (Mistral), larger model + low temperature
    # for a stricter, more consistent editorial judgment
    reviewer_llm = ChatMistralAI(model="mistral-large-latest", temperature=0.2)

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
        "WRITER · mistral-small &nbsp;|&nbsp; EDITOR · mistral-large</span>",
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
  <div class="meta">Vol. I · Drafted by Mistral · Reviewed by Mistral · Sourced via Tavily</div>
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
      <div>Give it a topic in the sidebar and hit <em>Send to the desk</em>.</div>
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

    # Copy button for the best/final draft
    best_draft = records[-1]["draft"].replace("`", "\\`").replace("\n", "\\n").replace("'", "\\'")
    st.markdown(f"""
    <button class="copy-btn" onclick="navigator.clipboard.writeText('{best_draft}')">📋 Copy latest draft</button>
    """, unsafe_allow_html=True)
