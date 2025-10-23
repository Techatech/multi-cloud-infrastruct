from google.adk.agents import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.tools import AgentTool
from pydantic import BaseModel, Field

# Import the tools we just defined
from app.tools import (
    query_best_practices,
    generate_ascii_diagram
)

# --- 1. Define the State Model ---
# This object holds the "memory" of the workflow as it passes
# from one agent to the next.

class InfrastructurePlan(BaseModel):
    """The data model for planning and executing an infrastructure request."""
    requirement: str = Field(description="The user's initial high-level requirement.")
    target_platform: str = Field(description="The cloud provider: 'aws', 'gcp', or 'azure'.")
    architecture_plan: str = Field(
        default="", 
        description="The detailed, multi-step architecture plan."
    )
    diagram_code: str = Field(
        default="", 
        description="The final Mermaid.js code for the architecture diagram."
    )
    cost_estimate: str = Field(
        default="", 
        description="The JSON report from the cost estimation API."
    )
    iac_code: str = Field(
        default="", 
        description="The final, complete Terraform HCL code."
    )

# --- 2. Define the Specialist Agents ---

# Specialist 1: The Planner
PlannerAgent = LlmAgent(
    name="PlannerAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are an expert Cloud Solutions Architect. Your goal is to create a "
        "detailed, secure, and production-ready architecture plan."
        "1. You will be given a high-level requirement and a target platform."
        "2. Use the high level requirement and target platform to determine  " 
        "   services needed and a Bill of Quantity. Be EXTREMELY concise "
        "        Format:                                                           "
        "        Services needed:                                                  "
        "        • Service 1 - reason (quantity)                                   "
        "        • Service 2 - reason (quantity)                                   "
        "        • Service 3 - reason (quantity)                                   "
        "3. You MUST use the `query_best_practices` tool to retrieve the "
        "   internal security and architecture guidelines from the knowledge base  "                                   
        "   for the individual services and how they must integrate."
        "4. You MUST incorporate these guidelines into your final plan "
        "5. Output a detailed plan with services and quantities. This plan will be used by "
        "   other agents to create diagrams, cost estimates, and code."
    ),
    tools=[query_best_practices],
    
)

# Specialist 2: The Diagrammer
DiagrammerAgent = LlmAgent(
    name="DiagrammerAgent",
    model="gemini-2.5-flash", 
    instruction=(
        "You are a specialist system diagrammer."
        "You will receive the current state which includes an architecture plan "
        "and the target platform."
        "You **MUST** call the `generate_ascii_diagram` tool, passing it the "
        "'architecture_plan' and 'target_platform' from the state."
        "Populate the 'diagram_code' field with the text diagram returned by the tool."
        "Do not add any other explanatory text yourself."
    ),
    tools=[generate_ascii_diagram], 
    
)

# Specialist 3: The Cost Estimator
CostAgent = LlmAgent(
    name="CostAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a FinOps (Financial Operations) specialist."
        "1. You will receive an architecture plan."
        "2. Your first task is to parse this plan and extract a detailed "
        "   list of all cloud resources and their specific configurations "
        "   (e.g., 'aws_instance' with 'instance_type: t3.large')."
        "3. use your general knowledge of cloud pricing for the target platform "
        "   to provide a **ROUGH ESTIMATED MONTHLY COST**. Include this estimate  "
        "   **State clearly that this is an approximation.** "
        "4. Your final output should be a cost report with line item cost and the total monthly cost."
    ), 
)

# Specialist 4: The Coder
CoderAgent = LlmAgent(
    name="CoderAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are an expert Infrastructure-as-Code (IaC) developer specializing "
        "in Terraform. You will be given a detailed architecture plan."
        "Your job is to write the complete, production-ready, and secure "
        "Terraform HCL code to deploy this architecture based *only* on the plan "
        "you created and your general knowledge of Terraform syntax for the target platform. "
        "Output the complete, valid `.tf` file content."
    ), 
)


# --- 3. Define the Sequential Workflow ---
# This agent runs the specialists in order, passing the state.

InfrastructureWorkflow = SequentialAgent(
    name="InfrastructureWorkflow",
    sub_agents=[
        PlannerAgent,
        DiagrammerAgent,
        CostAgent,
        CoderAgent
    ], 
)

# --- 4. Define the Root Orchestrator Agent ---
# This is the main agent the user talks to. Its only job
# is to clarify the request and then call the workflow tool.

root_agent = LlmAgent(
    name="OrchestratorAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a friendly and helpful Multi-Cloud Infrastructure Assistant."
        "Your goal is to help a user build and deploy cloud infrastructure."
        "1. First, get the user's high-level requirement (e.g., 'a web app')."
        "2. Second, you *MUST* ask for the 'target_platform' (aws, gcp, or azure) "
        "   if it is not already provided. Do not proceed without it."
        "3. Once you have both the requirement and the target_platform, you "
        "   MUST call the `run_infrastructure_workflow` tool to "
        "   execute the full build process."
        "4. Present the final plan, diagram, cost, and code to the user."
    ),
    tools=[
        # This is the advanced ADK pattern:
        # Wrap the entire workflow into a single "tool"
        # that the main conversational agent can call.
        AgentTool(
            agent=InfrastructureWorkflow,
        )
    ]
)