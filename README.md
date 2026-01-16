# Public Template for Docker MCP LLM GUI Application

This repository contains the **full demo application** from my <a href="https://youtu.be/DO3wPYJKpxk">Docker MCP YouTube Tutorial</a> — combining **Docker MCP Catalog**, **remote & local MCP servers**, and a **full-stack LLM web app** using **Docker Model Runner**.

It demonstrates how to:
- embed MCP tools into your own **Python application**,
- and build a **production-ready full-stack AI app** that calls MCP tools via a unified Docker gateway.

If you watched the video, this is the codebase used in the workflow.

---

## 🧠 What This App Does

- Uses the **Docker MCP Gateway** to unify access to both **local** and **remote MCP servers**.
- Calls real MCP tools (e.g., Stripe, DuckDuckGo, Hugging Face) from a Python app.
- Shows how Docker manages authentication, endpoints, and tool discovery.
- Builds a full-stack GUI AI app powered by **Docker Model Runner** + MCP.

This app serves as a **starter template** for building professional AI assistants with real tools.

---

## 🚀 Getting Started

### Prerequisites
- Docker Desktop (with MCP Toolkit & Catalog)
- Python 3.12+
- (Optional) Stripe account for remote Stripe MCP

---

## 📦 Setup Instructions

### 1. Clone the repository

```
git clone https://github.com/MariyaSha/Docker_MCPGUIApp.git
cd Docker_MCPGUIApp/complete_app
```

### 2. Configure environment variables

Rename the example file:

```
mv example.env .env
```

Edit `.env` and add your secrets:

```
STRIPE_SECRET_KEY="<YOUR SECRET KEY FROM STRIPE GOES HERE>"
```

---

### 3. Install a model in Docker Desktop

- Open **Docker Desktop**
- Go to **Models**
- Install a lightweight model (e.g. Gemma3)
- Update the model name in `.env` if you go for a different model

---

### 4. Build and run the app

```
docker compose up --build
```

Open your browser at:

```
http://localhost:8501
```

---

## 🧪 What You’ll See

- Calls to **local MCP tools** (DuckDuckGo) if you prompt for "search X on the web"
- Calls to **remote MCP tools** (Hugging Face) if you prompt for "search X on HuggingFace"
- Unified access via Docker MCP Gateway
- A full-stack AI web interface - the perfect template to develop your own LLM apps.

---

## 📚 Resources

- ⭐ Docker MCP Catalog: https://dockr.ly/4pzVKGd
---

## 💡 Notes

- Remote MCP servers authenticate via **browser-based OAuth**.
- Local MCP servers require API keys configured in Docker Desktop.
- Docker MCP Gateway still requires API Key authentication - may change in the future as Docker MCP is currently still in Beta.
- Applications only talk to **Docker MCP**, not individual MCP servers.

---

## ❤️ Contributing

Feel free to fork, extend, and reuse this project.

---

## 🧑‍💻 License

MIT License
