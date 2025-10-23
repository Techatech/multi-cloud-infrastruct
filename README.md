


# ☁️ Multi-Cloud Infrastructure Assistant 🤖

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/framework-Google%20ADK-orange.svg)](https://google.github.io/adk-docs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project demonstrates a multi-agent AI assistant built using Google's Agent Development Kit (ADK) to help plan, diagram, estimate costs (approximately), and generate Infrastructure-as-Code (IaC) templates for various cloud platforms (AWS, GCP, Azure).

---

## ✨ Features

* **Multi-Agent Architecture:** Uses specialized agents for planning, diagramming, and orchestration.
* **RAG Integration:** Leverages Elasticsearch as a knowledge base for cloud best practices and security guidelines using Retrieval-Augmented Generation.
* **Multi-Cloud:** Capable of generating plans and code for AWS, GCP, and Azure.
* **ASCII Diagrams:** Generates text-based architecture diagrams with emojis suitable for terminal/chat interfaces.
* **Approximate Cost Estimation:** Provides rough monthly cost estimates based on the generated plan using the Gemini model's knowledge.
* **IaC Generation:** Creates Terraform HCL code templates based on the generated plan and retrieved best practices.

---

## 🏗️ Architecture Overview

This assistant employs a multi-agent system (MAS) built with Google ADK:

1.  **`OrchestratorAgent`:** The main conversational agent. It interacts with the user, gathers requirements (like the desired infrastructure and target cloud platform), and invokes the main workflow.
2.  **`InfrastructureWorkflow` (`SequentialAgent`):** Executes the following specialist agents in order:
    * **`PlannerAgent` (`LlmAgent`):**
        * Uses the `query_best_practices` tool (Elasticsearch RAG) to retrieve relevant security/architecture guidelines from your knowledge base.
        * Uses the Gemini model, augmented with the RAG results, to generate a detailed architecture plan.
        * Uses Gemini's general knowledge to provide an *approximate* monthly cost estimate based on the plan.
        * Uses Gemini's general knowledge to generate the Terraform IaC code based on the plan.
    * **`DiagrammerAgent` (`LlmAgent`):**
        * Uses the `generate_ascii_diagram` tool to create a text-based diagram with emojis based on the plan and target platform.
3.  **Tools:**
    * **Elasticsearch RAG (`query_best_practices`):** Searches your pre-populated Elasticsearch indexes (`aws`, `gcp`, `azure`) for relevant best practice documents.
    * **ASCII Diagram Generator (`generate_ascii_diagram`):** Creates a text-based diagram renderable in the chat.
    * **Gemini Model:** Used by the `LlmAgent`s for reasoning, planning, cost estimation, and code generation.

*(Note: External tools for precise cost estimation (Infracost) and real-time Terraform syntax checking (Terraform MCP Server) were initially planned but have been removed in this version for simplicity.)*

---

## 🛠️ Setup Instructions

Follow these steps to set up and run the assistant locally:

### 1. Prerequisites

* **Python:** Version 3.10 or higher installed.
* **pip:** Python package installer.
* **Git:** For cloning the repository.
* **Elasticsearch Cloud Account:** A free or paid account at [cloud.elastic.co](https://cloud.elastic.co/).
* **Google AI Studio Account:** A Google account to access [aistudio.google.com](https://aistudio.google.com/).

### 2. Clone Repository

```bash
git clone <your-repository-url>
cd multi-cloud-assistant
````

### 3\. Set Up Python Environment

It's highly recommended to use a virtual environment:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the environment
# On Windows (Command Prompt/PowerShell)
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

# Install required packages (using the specific ADK version tested)
pip install -r requirements.txt
pip install google-adk==1.11.0 # Install the specific working version
```

### 4\. Configure Elasticsearch Cloud ☁️

1.  **Create Serverless Project:**
      * Log in to [cloud.elastic.co](https://cloud.elastic.co/).
      * Click "Create deployment" or find the option to create a **Serverless** project.
      * Choose the "Search" (or "Vector Search") solution type.
      * Follow the prompts to launch the project. **It deploys automatically.**
2.  **Get Credentials:**
      * During the *first-time setup*, Elastic will display an **API Key**. **Copy and save this securely\!** You'll need it for `ES_API_KEY`.
      * Once the project is running, navigate to its **Overview** page. Find the **Endpoint URL** (it looks like `https://your-project-alias.es.region.provider.cloud:port`). **Copy this URL.** You'll need it for `ES_ENDPOINT_URL`.
3.  **Create Indexes:**
      * In your Serverless project's Kibana interface, navigate to "Search" \> "Content" \> "Indices".
      * Click "Create index" and manually create three **empty** indexes with these exact names:
          * `aws`
          * `gcp`
          * `azure`
4.  **Deploy ELSER Model:**
      * Navigate to "Search" \> "Inference" \> "Trained Models".
      * Find the model named `.elser_model_...` (e.g., `.elser_model_2_linux-x86_64`).
      * Ensure its status is "Started" or "Deployed". If not, deploy it. **Note down this exact model ID.** You'll need it if you ever adjust the code (the current code assumes `.elser_model_2_linux-x86_64`).

### 5\. Configure Google AI Studio (Gemini API Key) 🔑

1.  Go to [Google AI Studio](https://aistudio.google.com/).
2.  Sign in with your Google account.
3.  Click "Get API key" on the left menu.
4.  If needed, create a new project.
5.  Click "Create new API key".
6.  **Copy the generated API key.** You'll need this for `GEMINI_API_KEY`.

### 6\. Configure `.env` File 📝

1.  Make a copy of the example environment file:

    ```bash
    # On Windows
    copy .env.example .env
    # On macOS/Linux
    cp .env.example .env
    ```

2.  Open the newly created `.env` file and paste your credentials:

    ```ini
    # .env

    # Your Google API key for the Gemini model
    GEMINI_API_KEY="PASTE_YOUR_GEMINI_KEY_HERE"

    # Your Elasticsearch Serverless credentials
    ES_ENDPOINT_URL="PASTE_YOUR_ELASTIC_ENDPOINT_URL_HERE"
    ES_API_KEY="PASTE_YOUR_ELASTIC_API_KEY_HERE"

    # No Terraform MCP URL or Cost API Key needed in this version
    ```

    *Make sure there are no extra spaces or quotes around the values.*

### 7\. Ingest Documentation into Elasticsearch 📚

1.  Place your cloud framework documents (PDFs) into the `docs/aws/`, `docs/gcp/`, and `docs/azure/` folders respectively.
2.  Run the ingestion script. This will chunk the PDFs and upload them to the correct Elasticsearch index, creating the necessary vector embeddings using ELSER.
    ```bash
    python ingest.py
    ```
    *This only needs to be run once, or whenever you update the documents.*

-----

## ▶️ Running the Application

1.  Ensure your Python virtual environment is activated.

2.  Make sure your `.env` file is correctly configured with your API keys.

3.  Run the ADK web server from the project root directory:

    ```bash
    adk web
    ```

4.  The server will start, typically on `http://127.0.0.1:8000`. Open this URL in your web browser.

5.  Select the `OrchestratorAgent` from the dropdown menu in the web UI.

6.  Start chatting\!

-----

## 💬 Usage Example

1.  **User:** `hi`
2.  **Agent:** `Hello! ... What kind of infrastructure do you need... And which cloud platform...?`
3.  **User:** `a scalable web application`
4.  **Agent:** `Great! ... Which cloud platform would you like to use: AWS, GCP, or Azure?`
5.  **User:** `AWS`
6.  **Agent:** *(Calls the workflow)* ... *(Waits while PlannerAgent runs RAG, generates plan/cost/code, and DiagrammerAgent generates diagram)* ... *(Presents the full results: Plan text, ASCII diagram, and Terraform code)*

-----

## 📝 Notes

  * **Cost Estimation:** The cost provided is an **approximation** based on Gemini's general knowledge and may not be accurate. Use official cloud provider calculators for detailed pricing.
  * **IaC Code:** The Terraform code is generated based on Gemini's knowledge and RAG results. It **should be reviewed** by a human for correctness and adherence to specific organizational standards before deployment. Real-time syntax validation (via Terraform MCP) is not included in this version.
  * **Diagram Rendering:** The ASCII diagram uses text and emojis. Visual rendering depends on the capabilities of the interface displaying it. It should look correct in the ADK web UI's monospaced text output.
  * **ADK Version:** This code was tested and debugged primarily with `google-adk==1.11.0`. Newer versions might require adjustments to import paths or class arguments due to library updates.

<!-- end list -->

```
```
