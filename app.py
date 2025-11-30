import os
import asyncio
import streamlit as st
from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

##############################
# LLM & MCP SETTINGS
##############################

BASE_URL = os.environ.get("BASE_URL")
MODEL_NAME = os.environ.get("MODEL_NAME")
LOCAL_MCP_HOST = os.environ.get("LOCAL_MCP_HOST")
REMOTE_MCP_HOST = os.environ.get("REMOTE_MCP_HOST")

llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key="nope",
    base_url=BASE_URL,
)

##############################
# REMOTE MCP
##############################

async def search_paper(query):
    """Call the Hugging Face MCP `paper_search` tool via its own gateway."""

    async with streamablehttp_client(REMOTE_MCP_HOST) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("paper_search", {"query": query})
            block = result.content[0]
            text = getattr(block, "text", None) or "[MCP] paper_search returned no text."
            return text

def run_search_paper(query):
    return asyncio.run(search_paper(query))

##############################
# SEARCH TOPIC EXTRACTION
##############################

def get_search_topic(prompt, mode="paper"):
    """
    Extract X from:
        - "... search X on hugging face ..."
        - "... search X on the web ..."
    depending on mode.
    """

    lower = prompt.lower()

    if mode == "paper":
        end_key_options = ["on hugging face", "on hf", "on the hugging face"]
    elif mode == "web":
        end_key_options = ["on the web", "on web", "on internet"]
    else:
        return None

    start_key = "search"

    i_start = lower.find(start_key)
    if i_start == -1:
        return None

    i_end = None
    for ek in end_key_options:
        pos = lower.find(ek)
        if pos != -1:
            i_end = pos
            break

    if i_end is None or i_end <= i_start:
        return None

    start_idx = i_start + len(start_key)
    topic = prompt[start_idx:i_end]
    topic = topic.strip(" :,-\n\t")
    return topic or None

##############################
# LOCAL MCP (WEB SEARCH)
##############################
async def web_search(query):
    try:
        async with streamablehttp_client(LOCAL_MCP_HOST) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool("search", {"query": query})
                block = result.content[0]
                text = getattr(block, "text", None)
                return text or "[MCP] DuckDuckGo search returned non-text content."

    except Exception as e:
        return f"[MCP] DuckDuckGo search failed: {e!r}"

def run_web_search(query):
    return asyncio.run(web_search(query))

##############################
# GUI
##############################

st.title("Talk to me...")
st.text("search X on the web | search X on hugging face")

think_harder = st.checkbox("Think harder...", value=False)

st.session_state.setdefault("messages", [])

# Show chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("type your message...")

if prompt:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Use only the last few messages as context
    history_window = 6
    history = st.session_state["messages"][-history_window:]

    context = ""
    for msg in history:
        context += f"{msg['role']}: {msg['content']}\n"

    ##############################
    # PAPER SEARCH
    ##############################
    paper_topic = get_search_topic(prompt, mode="paper")
    research_text = ""

    if paper_topic:
        research_text = run_search_paper(paper_topic)

        # truncation of text over 10000 characters
        if len(research_text) > 10000:
            research_text = research_text[:10000] + "\n...[truncated]"

        context += (
            "assistant: Here are research papers from Hugging Face relevant to "
            f"the topic '{paper_topic}':\n\n"
            f"{research_text}\n\n"
            "assistant: Based on the above research, answer the user's last question.\n"
        )

    ##############################
    # WEB SEARCH
    ##############################
    web_topic = get_search_topic(prompt, mode="web")
    web_text = ""

    if web_topic:
        web_text = run_web_search(web_topic)

        context += (
            f"\nassistant: Here is a DuckDuckGo web search result "
            f"for the topic '{web_topic}':\n\n"
            f"{web_text}\n\n"
        )

    ##############################
    # LLM RESPONSE
    ##############################
    response = llm.invoke(context)
    final_text = response.content

    # Store only the main answer in history
    st.session_state["messages"].append({"role": "assistant", "content": final_text})

    with st.chat_message("assistant"):
        st.write(final_text)

        if paper_topic and research_text:
            with st.expander(
                f"📚 Research Sources (Hugging Face `paper_search` on '{paper_topic}')"
            ):
                st.write(research_text)

        if web_topic and web_text:
            with st.expander(
                f"🔎 Web Search Results (DuckDuckGo `search` on '{web_topic}')"
            ):
                st.write(web_text)
