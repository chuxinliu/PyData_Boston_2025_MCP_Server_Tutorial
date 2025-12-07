# Build Your MCP Server

**PyData Boston 2025 Tutorial**  
Monday, December 8, 11:00 AM

**Instructors**: [Chuxin Liu](https://www.linkedin.com/in/chuxin-liu/) and [Yiwen Liu](https://www.linkedin.com/in/yiwen-liu-cssbb-24902016/)

## Project Description

This project demonstrates building an MCP server that integrates with Gmail, allowing AI agents to:
- Read unread emails from a Gmail inbox
- Generate AI-powered email replies using OpenAI
- Send emails via Gmail SMTP

The server uses the FastMCP framework to expose these capabilities as MCP tools and prompts.

## Project Structure

```
pydata_mcp_tutorial/
├── gmail_mcp_server_questions.py # Exercise version with placeholders
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## Setup Instructions

### 1. Install uv

Install `uv`, a fast Python package installer and resolver:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Initialize Project

Initialize a new uv project:

```bash
uv init
```

### 3. Create Virtual Environment

Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate
```

### 4. Install Dependencies

Add the required dependencies:

```bash
uv add mcp openai
```

### 5. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_APP_PASSWORD=your-gmail-app-password
OPENAI_API_KEY=your-openai-api-key
```

**Gmail App Password Setup:**
1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Enable 2-Step Verification (if not already enabled)
3. Generate an App Password 
4. Use this 16-character password in `EMAIL_APP_PASSWORD`

### 6. Run the MCP Server

Run the server using the MCP Inspector:

**If running on GitHub Codespaces:**

```bash
ALLOWED_ORIGINS=https://your-codespace-url-6274.app.github.dev npx @modelcontextprotocol/inspector uv run gmail_mcp_server_questions.py
```

Replace `your-codespace-url` with your actual Codespace URL.

Inspector Proxy Address: https://your-codespace-url-6277.app.github.dev

**If running locally:**

```bash
npx @modelcontextprotocol/inspector uv run gmail_mcp_server_questions.py
```

The server runs on stdio transport and communicates via JSON-RPC. The MCP Inspector provides a web interface to test and interact with your MCP server.

## Available MCP Tools

### `read_unread_emails`
Reads unread emails from your Gmail inbox.

**Parameters:**
- `max_results` (int, default: 5): Maximum number of emails to retrieve

**Returns:** Dictionary with `unread_emails` list containing `from_address`, `subject`, and `body` for each email.

### `write_reply`
Generates an AI-powered email reply using OpenAI.

**Parameters:**
- `original_email_body` (str): The body of the email to reply to
- `prompt` (str, optional): Custom persona instructions (defaults to email agent persona)

**Returns:** Dictionary with `reply` text.

### `send_email`
Sends an email via Gmail SMTP.

**Parameters:**
- `to` (str): Recipient email address
- `subject` (str): Email subject
- `body` (str): Email body content

**Returns:** Dictionary with `status: "sent"`.

## Available MCP Prompts

### `email_agent_persona`
Returns a persona prompt for an email agent that loves food and dislikes exercise. This prompt guides the AI's behavior when generating email replies.

---

This tutorial project is provided for educational purposes.
