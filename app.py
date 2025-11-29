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

async def _remote_paper_search_async(query: str) -> str:
    """Call the Hugging Face MCP `paper_search` tool via its own gateway."""
    if not REMOTE_MCP_HOST:
        return "[MCP] REMOTE_MCP_HOST is not set in the environment."

    async with streamablehttp_client(REMOTE_MCP_HOST) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("paper_search", {"query": query})

            if not result.content:
                return "[MCP] No content returned from Hugging Face paper_search."

            block = result.content[0]
            text = getattr(block, "text", None) or "[MCP] paper_search returned no text."
            return text

def remote_paper_search(query: str) -> str:
    """Sync wrapper so we can call MCP from Streamlit."""
    return asyncio.run(_remote_paper_search_async(query))

def extract_hf_research_topic(prompt: str) -> str | None:
    """
    Extract X from:
        ... search X on hugging face ...
    Case-insensitive.
    """
    lower = prompt.lower()
    start_key = "search"
    end_key = "on hugging face"

    i_start = lower.find(start_key)
    i_end = lower.find(end_key)

    if i_start == -1 or i_end == -1 or i_end <= i_start:
        return None

    start_idx = i_start + len(start_key)
    topic = prompt[start_idx:i_end]
    topic = topic.strip(" :,-\n\t")
    return topic or None

##############################
# LOCAL MCP
##############################

async def _search_web_async() -> str:
    """
    MCP client for DuckDuckGo via its own gateway:
    - connects to MCP_HOST (DDG gateway)
    - lists tools
    - calls 'web_search' with query='Docker' if available
    """
    if not LOCAL_MCP_HOST:
        return "[MCP] LOCAL_MCP_HOST is not set in the environment."

    try:
        async with streamablehttp_client(LOCAL_MCP_HOST) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # NOTE: list_tools returns a *response* object
                tools_response = await session.list_tools()
                tools = getattr(tools_response, "tools", tools_response)

                tool_names = [t.name for t in tools]

                # DuckDuckGo exposes 'web_search' and 'get_page_content'
                if "web_search" in tool_names:
                    tool_name = "web_search"
                elif "search" in tool_names:
                    tool_name = "search"
                else:
                    return (
                        "[MCP] No suitable search tool found on DuckDuckGo gateway.\n"
                        f"Available tools: {', '.join(tool_names)}"
                    )

                result = await session.call_tool(tool_name, {"query": "Docker"})
                if not result.content:
                    return "[MCP] Search tool returned no content."

                block = result.content[0]
                text = getattr(block, "text", None)
                return text or "[MCP] Search tool returned non-text content."
    except Exception as e:
        return f"[MCP] DuckDuckGo search failed: {e!r}"

def search_web() -> str:
    """Sync wrapper for Streamlit."""
    return asyncio.run(_search_web_async())

##############################
# GUI
##############################

st.title("Talk to me... (with Hugging Face MCP research)")

think_harder = st.checkbox("Think harder...", value=False)

# Tiny sanity check for beginners
st.sidebar.header("MCP Debug")
st.sidebar.write(f"LOCAL_MCP_HOST: `{LOCAL_MCP_HOST}`")

st.session_state.setdefault("messages", [])

# Show chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("type your message...")

if prompt:
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Use only the last few messages as context
    history_window = 6
    history = st.session_state["messages"][-history_window:]

    context = ""
    for msg in history:
        context += f"{msg['role']}: {msg['content']}\n"

    # Look for: "research X on hugging face"
    research_topic = extract_hf_research_topic(prompt)
    research_text = ""

    if research_topic:
        research_text = remote_paper_search(research_topic)

        # Truncate research before sending to LLM to stay under context limit
        truncated_research = research_text
        max_chars = 4000
        if len(truncated_research) > max_chars:
            truncated_research = truncated_research[:max_chars] + "\n...[truncated]"

        context += (
            "\nassistant: Here are research papers from Hugging Face relevant to "
            f"the topic '{research_topic}':\n\n"
            f"{truncated_research}\n\n"
            "assistant: Based on the above research, answer the user's last question. "
            "Use the research as your factual grounding but respond in your own words.\n"
        )

    # If user says "search web", hit DuckDuckGo via MCP
    if "search web" in prompt.lower():
        result_text = search_web()
        context += (
            "\nassistant: Here is a DuckDuckGo web search result (query='Docker'):\n\n"
            f"{result_text}\n\n"
        )

        # optional: show raw MCP output
        st.sidebar.write("DuckDuckGo raw result:")
        st.sidebar.write(result_text)

    # Ask the LLM
    response = llm.invoke(context)
    final_text = response.content

    # Show research sources under the answer (if any)
    if research_topic and research_text:
        final_text += (
            "\n\n---\n"
            f"📚 **Research Sources (Hugging Face `paper_search` on '{research_topic}')**:\n"
            f"{research_text}"
        )

    # Add assistant message
    st.session_state["messages"].append(
        {"role": "assistant", "content": final_text}
    )
    with st.chat_message("assistant"):
        st.write(final_text)
