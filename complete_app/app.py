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
    # connect to different MCP Gateways
    async with streamablehttp_client(host) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            # call different tools with optional arguments
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
        # using hugging face server
        result = await call_mcp(REMOTE_MCP_HOST, "paper_search", {"query": query}) 

    elif mode == "web": 
        # using duckduckgo server
        result = await call_mcp(LOCAL_MCP_HOST, "search", {"query": query})
    return getattr(
        result.content[0],
        "text",
        f"[MCP] returned non-text content."
    )

###############################################
# EXTRACT SEARCH TOPIC FROM PROMPT
###############################################
def get_search_topic(prompt, mode):
    """"
    Detect pattern "search X on Y" and extract X
    - prompt: user input string
    - mode: "paper" for hugging face paper search
            "web" for duck duck go web search
    """
    p = prompt.lower()
    i_start = p.find("search")

    if i_start == -1:
        # "search" is not in prompt
        return None

    patterns = {
        "paper": ["on hugging face", "on hf", "on the hugging face"],
        "web":   ["on the web", "on web", "on internet"],
    }
    
    # fetch index of the last character: "h"
    i_start += len("search")

    # search for end keywords based on mode
    for end_key in patterns[mode]:
        i_end = p.find(end_key)
        if i_end > i_start:
            # ecxtract topic between "search" and the end keywords
            return prompt[i_start:i_end].strip() or None  # <- strip spaces

    return None

def is_mcp_search_required(context, prompt, mode):
    """
    Determine if MCP search is needed and run it.
    - context: current chat history string
    - prompt: latest user input string
    - mode: "paper" for hugging face paper search
            "web" for duck duck go web search
    """
    topic = get_search_topic(prompt, mode)
    text = ""

    if topic:
        # run MCP search
        text = asyncio.run(mcp_search(mode, topic))

        # truncate if needed
        if len(text) > 8000:
            text = text[:8000] + "\n...[truncated]"

        # use context message
        context += (
            "assistant: Here are results from a search tool "
            f"for the topic '{topic}':\n\n"
            f"{text}\n\n"
        )

    return context, topic, text

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

    ################## Unified Paper Search ##################
    context, paper_topic, research_text = is_mcp_search_required(context, prompt, "paper")

    ################## Unified Web Search ##################
    context, web_topic, web_text = is_mcp_search_required(context, prompt, "web")

    # If we ran at least one search, add a single follow-up instruction
    if paper_topic or web_topic:
        context += (
            "assistant: Based on the search results above, "
            "answer the user's latest request in a helpful way.\n"
        )

    ################## LLM Response ##################
    response = llm.invoke(context)
    final_text = response.content

    # Store only the main answer in history
    st.session_state["messages"].append({"role": "assistant", "content": final_text})

    with st.chat_message("assistant"):
        st.write(final_text)

    # Display Expanding Search Results
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
