import os
import google.generativeai as genai
from dotenv import load_dotenv

# Import the root_agent from your agent.py file
from app.agent import root_agent

def main():
    """
    Main entrypoint for the Multi-Cloud Infrastructure Assistant.
    
    This function loads environment variables and configures the 
    Gemini API key. It no longer starts the web server directly.
    """
    print("Configuring Multi-Cloud Assistant...")
    
    # Load environment variables from .env file
    load_dotenv()

    # Configure the Gemini API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)

    print("Gemini API key configured.")
    print("Setup complete.")
    print("Please run the agent using the ADK CLI: 'adk web'")

if __name__ == "__main__":
    main()

# --- Important ---
# Make sure your root_agent is correctly defined and imported in app/agent.py
# The ADK CLI will look for it there.