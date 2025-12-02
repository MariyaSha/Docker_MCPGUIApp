import os
import asyncio
import streamlit as st
from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

###############################################
# LLM & MCP SETTINGS
###############################################
# Environment variable names from .env
BASE_URL = os.environ.get("BASE_URL")
MODEL_NAME = os.environ.get("MODEL_NAME")
LOCAL_MCP_HOST = os.environ.get("LOCAL_MCP_HOST")
REMOTE_MCP_HOST = os.environ.get("REMOTE_MCP_HOST")

# Initialize LLM via Docker Model Runner
llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key="nope",
    base_url=BASE_URL,
)

###############################################
# SHARED MCP CALL HELPER
###############################################
async def call_mcp(host, tool, args):
    """
    Call a tool from Docker MCP Gateways.
    - host: REMOTE_MCP_HOST or LOCAL_MCP_HOST
    - tool: string of tool name
    - args: dict of tool arguments or {}
    """
    async with streamablehttp_client(host) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            result = await session.call_tool(tool, args)
            return result

###############################################
# GENERIC MCP SEARCH (PAPER OR WEB)
###############################################
async def mcp_search(mode, query):
    """
    Search Term on Different Mediums via MCP.
    mode:
      - "paper": Hugging Face paper_search for REMOTE_MCP_HOST
      - "web": DuckDuckGo search for LOCAL_MCP_HOST
    """
    if mode == "paper":
        host = REMOTE_MCP_HOST
        tool = "paper_search"

    elif mode == "web":
        host = LOCAL_MCP_HOST
        tool = "search"
    
    result = await call_mcp(host, tool, {"query": query})

    if not result.content:
        return f"[MCP] returned no content."

    c = result.content[0]
    return getattr(
        c,
        "text",
        f"[MCP] returned non-text content."
    )

###############################################
# EXTRACT SEARCH TOPIC FROM PROMPT
###############################################
def get_search_topic(prompt, mode):
    """"Detect "search X on Y" and extract X"""
    p = prompt.lower()

    patterns = {
        "paper": ["on hugging face", "on hf", "on the hugging face"],
        "web":   ["on the web", "on web", "on internet"],
    }

    # search for "search" in prompt
    # fetch index of the first character: "s"
    i_start = p.find("search")

    if i_start == -1:
        # "search" is not in prompt
        return None
    
    # fetch index of the last character: "h"
    i_start += len("search")

    # search for end keywords based on mode
    for end_key in patterns[mode]:
        i_end = p.find(end_key)
        if i_end > i_start:
            # ecxtract topic between "search" and the end keywords
            return prompt[i_start:i_end] or None

    return None

###############################################
# GUI APPLICATION
###############################################
st.title("Talk to me...")
st.text("search X on the web | search X on hugging face")

# start collecting messages
st.session_state.setdefault("messages", [])

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Collect user input
prompt = st.chat_input("type your message...")

if prompt:
    # Store and Display user message
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Use only the last few messages as context (optional)
    history = st.session_state["messages"][-10:]

    # Convert messages to a single string
    context = ""
    for msg in history:
        context += f"{msg['role']}: {msg['content']}\n"

    ################## Peper Search ##################
    paper_topic = get_search_topic(prompt, mode="paper")
    research_text = ""

    if paper_topic:
        research_text = asyncio.run(mcp_search("paper", paper_topic))

        # truncation of text over 8000 characters
        if len(research_text) > 8000:
            research_text = research_text[:8000] + "\n...[truncated]"

        context += (
            "assistant: Here are research papers from Hugging Face relevant to "
            f"the topic '{paper_topic}':\n\n"
            f"{research_text}\n\n"
            "assistant: Based on the above research, answer the user's last question.\n"
        )

    ################## Web Search ##################
    web_topic = get_search_topic(prompt, mode="web")
    web_text = ""

    if web_topic:
        web_text = asyncio.run(mcp_search("web", web_topic))

        context += (
            f"\nassistant: Here is a DuckDuckGo web search result "
            f"for the topic '{web_topic}':\n\n"
            f"{web_text}\n\n"
        )

    ################## LLM Response ##################
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
