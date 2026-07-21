# 🖋️ The Byline Desk

**An AI writer drafts. A stricter AI editor won't sign off until it's right.**

The Byline Desk is a LangGraph-powered pipeline that turns a single topic into a publish-ready LinkedIn post. A writer agent drafts the post (pulling live web context when needed), a stricter editor agent reviews it against a fixed rubric, and the two go back and forth — writer revises, editor re-reviews — until the post is approved or a revision cap is hit. Every round is shown in a newsroom-styled Streamlit UI, stamped **APPROVED** or **REJECTED** like a real copy desk.

**🔗 Live app:** [the-byline-desk-r8ep9szw2sn23hkwg49ubh.streamlit.app](https://the-byline-desk-r8ep9szw2sn23hkwg49ubh.streamlit.app/)

---

## How it works

```
        ┌────────────┐        needs current info?        ┌────────────┐
 START ─▶   Writer    │───────────────────────────────────▶  Tavily    │
        │ (Mistral)  │◀───────────────────────────────────│  Search    │
        └────────────┘                                     └────────────┘
              │
              ▼
        ┌────────────┐
        │  Extract    │
        │   Draft     │
        └────────────┘
              │
              ▼
        ┌────────────┐   rejected & attempts left   ┌────────────┐
        │  Reviewer   │──────────────────────────────▶  back to   │
        │  (Gemini)   │                               │  Writer    │
        └────────────┘                               └────────────┘
              │
   approved OR max attempts reached
              │
              ▼
             END
```

- **Writer** — `mistral-small-2506` via `ChatMistralAI`. Drafts the post, and can call a Tavily web search tool first if the topic needs current facts or stats. On a retry, it's fed the editor's exact feedback and told to fix every point raised.
- **Reviewer** — `gemini-2.5-flash` via `ChatGoogleGenerativeAI`. Scores the draft against a fixed rubric (hook, one takeaway, skimmability, ~150–200 words, CTA/question ending, tone, no hashtags) and returns a strict `VERDICT` + `FEEDBACK`.
- **Loop control** — the graph keeps cycling writer → reviewer until the reviewer approves or the configurable revision cap is reached, whichever comes first.

The whole thing is a compiled [LangGraph](https://langchain-ai.github.io/langgraph/) `StateGraph`, wrapped in a Streamlit front end that streams each step live and renders every revision as a "manuscript" card with an editor's stamp.

---

## Features

- 🔁 Multi-round writer ↔ editor revision loop with a configurable max (1–5 rounds)
- 🔍 Writer can search the web via Tavily before drafting, for topics needing current data
- 📝 Every revision is kept and shown, not just the final draft — so you can see what changed and why
- ✅ / ❌ Visual approve/reject stamps and per-round editor feedback ("red pen" notes)
- 📊 Live word count per draft, round tracker, and a real-time status log while the graph runs
- 📋 One-click copy of the final draft, plus a `.txt` download button
- 🎨 Custom dark green & black "newsroom" theme, built entirely in CSS injected into Streamlit

---

## Tech stack

| Layer | Tool |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| Writer LLM | Mistral (`mistral-small-2506`) via `langchain-mistralai` |
| Reviewer LLM | Google Gemini (`gemini-2.5-flash`) via `langchain-google-genai` |
| Web search tool | [Tavily](https://tavily.com/) via `langchain-tavily` |
| UI | [Streamlit](https://streamlit.io/) |
| Deployment | Streamlit Community Cloud |

---

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/the-byline-desk.git
cd the-byline-desk
```

### 2. Install dependencies

```bash
pip install streamlit langgraph langchain-mistralai langchain-google-genai langchain-tavily
```

*(or `pip install -r requirements.txt` if you've committed one)*

### 3. Add your API keys

The app reads keys from environment variables (or Streamlit secrets). Create a `.env` file locally:

```
MISTRAL_API_KEY=your_mistral_key
GOOGLE_API_KEY=your_google_key
TAVILY_API_KEY=your_tavily_key
```

| Key | Get it from |
|---|---|
| `MISTRAL_API_KEY` | [console.mistral.ai](https://console.mistral.ai/) |
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/) |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com/) |

For **Streamlit Cloud** deployment, add the same three keys under **App settings → Secrets** instead of a `.env` file — the app checks `st.secrets` automatically and falls back to environment variables.

### 4. Run it

```bash
streamlit run app.py
```

*(replace `app.py` with your actual filename, e.g. `byline_desk.py`)*

---

## Usage

1. Open the sidebar and enter a topic (e.g. *"why most technical interviews test the wrong thing"*).
2. Pick how many revision rounds you want to allow (1–5).
3. Click **Send to the desk →**.
4. Watch the writer draft, the editor review, and — if rejected — the writer revise, live in the status ticker.
5. Once approved (or the round cap is hit), every draft is shown as a manuscript card with the editor's verdict and notes. Copy or download the final one.

---

## Project structure

```
.
├── app.py              # Streamlit app: graph definition + UI
├── requirements.txt    # Python dependencies
└── README.md
```

---

## License

MIT — feel free to fork, adapt, and build on it.
