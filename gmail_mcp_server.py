# -------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------

from mcp.server.fastmcp import FastMCP # MCP SDK
from openai import OpenAI # OpenAI SDK

import smtplib, imaplib, os
# from email.mime.text import MIMEText
from email import message_from_bytes
from email.header import decode_header
from email.message import EmailMessage

from dotenv import load_dotenv


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()

# Gmail
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
IMAP_SERVER = "imap.gmail.com"
SMTP_PORT = 587

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Create the MCP server
mcp = FastMCP("Gmail Tutorial Server")


# -------------------------------------------------------------------
# Helper functions (Gmail + OpenAI)
# -------------------------------------------------------------------

def _decode_header(value: str | None) -> str:
    """Decode email header (From, Subject, etc.)"""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    return "".join([text.decode(enc or "utf-8") if isinstance(text, bytes) else text 
                    for text, enc in decoded_parts])


def _extract_text_body(msg) -> str:
    """Get the plain-text body from an email."""
    def decode_payload(payload_bytes, charset=None):
        """Decode email payload with fallback encodings."""
        if payload_bytes is None:
            return ""
        
        # Try charset from email, then common encodings
        encodings = []
        if charset:
            encodings.append(charset)
        encodings.extend(["utf-8", "latin-1", "iso-8859-1", "windows-1252", "cp1252"])
        
        for encoding in encodings:
            try:
                return payload_bytes.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Last resort: decode with errors='replace' to avoid crashing
        return payload_bytes.decode("utf-8", errors="replace")
    
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return decode_payload(payload, charset)
    
    payload = msg.get_payload(decode=True)
    charset = msg.get_content_charset() or "utf-8"
    return decode_payload(payload, charset)


def _generate_reply(email_body: str, persona_instructions: str) -> str:
    """Call OpenAI to generate a reply."""
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": persona_instructions},
            {"role": "user", "content": email_body}
        ]
    )
    return response.choices[0].message.content


# -------------------------------------------------------------------
# MCP prompt: the persona of your email agent
# -------------------------------------------------------------------

@mcp.prompt()
def email_agent_persona() -> str:
    """
    Returns a short persona prompt for an email agent who loves food and dislikes exercise.
    """
    return (
        "You are an email agent.\n"
        "- You love food and hanging out over meals.\n"
        "- You dislike exercise and running.\n"
        "- If the email invites you to lunch or food: respond with an enthusiastic YES.\n"
        "- If the email invites you to run, work out, or exercise: respond with a polite NO "
        "and suggest grabbing food instead.\n"
        "- Always keep your reply friendly, short, and in plain text.\n"
    )


# -------------------------------------------------------------------
# MCP tools: read, write reply, send
# -------------------------------------------------------------------

@mcp.tool(name="read unread emails", description="Read unread emails from Gmail inbox, returning a list of sender, subject, and body for each.")
def read_unread_emails(max_results: int = 5) -> dict[str, list[dict[str, str]]]:
    """
    Read unread emails from Gmail inbox..

    Returns a list of simple dicts:
    - from_address
    - subject
    - body
    """
    results = []

    with imaplib.IMAP4_SSL(IMAP_SERVER) as imap:
        imap.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        imap.select("INBOX")

        # Use SORT to get newest unread emails first (more efficient than fetching all IDs)
        # SORT returns newest first, so we only need the first max_results
        try:
            _, data = imap.sort("(REVERSE DATE)", "UTF-8", "UNSEEN")
            if not data or not data[0]:
                return []
            # SORT returns newest first, take first max_results
            message_ids = data[0].split()[:max_results]
        except imaplib.IMAP4.error:
            # Fallback if SORT not supported (shouldn't happen with Gmail)
            _, data = imap.search(None, "UNSEEN")
            if not data or not data[0]:
                return []
            # Take last max_results (newest) and reverse to get newest first
            all_ids = data[0].split()
            message_ids = all_ids[-max_results:][::-1]
        
        for message_id in message_ids:
            _, msg_data = imap.fetch(message_id, "(BODY.PEEK[])")
            if not msg_data:
                continue

            msg = message_from_bytes(msg_data[0][1])
            results.append({
                "from_address": _decode_header(msg.get("From")),
                "subject": _decode_header(msg.get("Subject")),
                "body": _extract_text_body(msg),
            })

    return {"unread_emails": results}


@mcp.tool(name="write_reply", description="Use the email agent persona, received email and LLM to write a reply")
def write_reply(original_email_body: str, prompt: str = None) -> dict[str, str]:
    """
    Generate an email reply using the email agent persona and OpenAI LLM.

    Args:
        original_email_body: Plain text body of the original email to reply to
        prompt: Optional persona prompt instructions. If not provided, uses the default email_agent_persona()

    Returns:
        A dictionary containing:
        - reply: The generated reply text that can be passed directly to send_email()
        
    Example:
        >>> result = write_reply("Would you like to grab lunch?")
        >>> result["reply"]  # Use this with send_email()
    """
    if prompt is None:
        prompt = email_agent_persona()
    
    reply_text = _generate_reply(email_body=original_email_body, persona_instructions=prompt)
    
    return {"reply": reply_text}

@mcp.tool(name="send_email", description="Send an email via Gmail SMTP")
async def send_email(to: str, subject: str, body: str):
    """
    Send an email via Gmail SMTP. 

    Inputs:
    - to_address: recipient's email address
    - subject: email subject
    - body: plain text body
    """
    # msg = MIMEText(body)
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to    
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)

    return {"status": "sent"}


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
