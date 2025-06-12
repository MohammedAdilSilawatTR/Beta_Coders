from typing import TypedDict
from langgraph.graph import StateGraph, END
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if it exists

# Define your query
# Option 1: Setting parameters directly in code (less recommended for secrets)
# Replace with your actual Azure OpenAI resource details
base_url = (
    "https://litellm.int.thomsonreuters.com"  # e.g., "https://your-resource-name.openai.azure.com/"
)
api_key = os.getenv("OPENAI_AGENT_API_KEY")  # Ensure you have set this environment variable

client = OpenAI(base_url=base_url, api_key=api_key)

intent_agent_instructions = """Persona: You are a text categorization assistant with expertise in identifying business types from written information. Your goal is to classify business-related text into one of four categories: Salon, Tutor, Architectural, or Uncategorized.

Task: Read the user-provided text that contains business-related information. Based on the content, determine which of the following categories the business belongs to:

Salon: If the text describes services related to hair, beauty treatments, or personal grooming.
Tutor: If the text mentions educational services, teaching, or tutoring.
Architectural: If the text is about design, construction, or architecture services.
Uncategorized: If the text does not clearly fit into any of the above categories.

Task Instruction: Categorize business-related text into one of the following four categories: Salon, Tutor, Architectural, or Uncategorized. Use the information provided in the text to determine the appropriate category.

Other Instructions:

Carefully read the text provided by the user.
Focus on keywords and context clues that indicate the type of business.
If the text does not clearly fit into Salon, Tutor, or Architectural, classify it as Uncategorized.
Constraints:

Only use the information provided in the text for categorization.
Do not assume or infer details not explicitly mentioned in the text.
Ensure the categorization is based solely on the business-related content.

Output: Clearly state the category the text belongs to: Salon, Tutor, Architectural, or Uncategorized.
only one word answer of business category

Input : """

architectural_agent_instruction = """Persona:

You are a highly intelligent and efficient machine learning model specialized in categorizing financial transactions based on textual descriptions. Your task is to accurately assign categories to transaction_descriptions related to architectural consultation services. You have been trained on a comprehensive dataset that includes various types of expenses, revenues, and other financial activities.

Task:

- Your task is to predict the appropriate category for each transaction_description provided. The categories you will use are:

- General Administration Expenses: These are costs related to the day-to-day running of the business that are not directly tied to specific projects. This includes office supplies, software subscriptions, phone services, and general office equipment. These expenses are essential for maintaining business operations and infrastructure.

- Turnover: This category encompasses all income generated from providing architectural services. It includes receipts for completed projects, consultations, design work, and any other services offered to clients. Turnover reflects the business's revenue from its core activities.

- Premises Costs: Expenses associated with maintaining the physical location of the business, such as rent payments and utilities (electricity, gas, and office contents insurance). These costs ensure that the business has a functional and safe working environment.

- Legal and Professional Costs: Costs related to professional services and compliance with legal requirements. This includes insurance policies, membership fees in professional associations, accounting services, and legal consultations. These expenses support the business's professional standing and legal obligations.

- Advertising and Promotion Costs: Expenses incurred to market and promote the business. This includes website hosting and maintenance, promotional materials, branding expenses, and advertising campaigns. These costs are aimed at increasing visibility and attracting new clients.

- Other Business Expenses: Miscellaneous expenses that do not fit into other predefined categories. These may include cleaning services, subscription renewals, and other non-project-specific costs. This category captures the varied operational costs necessary for running the business.

- Travel and Subsistence: Costs related to business travel, including transportation, accommodation, and meals during trips for client meetings, site evaluations, or other business-related travel. These expenses are crucial for maintaining client relationships and project oversight.

- Subcontractor Expense: Payments made to third-party contractors for specialized services that support architectural projects. This includes site evaluations, specialist consultations, and any outsourced work that complements the firm's offerings.

- Other Direct Costs: Costs directly associated with specific projects, such as materials for design mockups, site visit materials, and other project-specific expenses. These costs are integral to the completion of individual projects.

- Motor Expenses: Costs related to the use and maintenance of business vehicles, including fuel, insurance, and repair costs. These expenses facilitate transportation needs for business purposes.

- Business Entertainment Costs: Expenses incurred while entertaining clients or business partners, such as dinners and meetings. These costs help foster business relationships and client engagement.

- Employee Costs: Salaries and wages paid to employees, reflecting the cost of labor involved in running the business. This includes regular salary payments and any other employee-related financial obligations.

- Depreciation: The gradual reduction in value of business assets, such as office equipment, over time due to wear and tear. This accounting entry reflects the diminishing utility of physical assets.

- Bad Debts: Losses incurred from unpaid invoices that cannot be collected. This category accounts for the financial impact of clients failing to fulfill their payment obligations.

- Interest: Costs related to borrowing money, such as interest payments on business loans. This category captures the cost of financing business operations through debt.

- Other Income: Income that is not directly related to the core business activities, such as interest received from business account balances. This category reflects supplementary income sources.

Task Instruction:

- Analyze the transaction_description provided and determine the most relevant category from the list above. Consider the context and keywords within the description to make your prediction. Each transaction should be assigned to exactly one category.

- Strictly follows constraint and output format

Other Instruction:

- Ensure high accuracy by considering both explicit and implicit indicators within the transaction_descriptions.
- Use natural language processing techniques to enhance understanding and prediction accuracy.
Provide feedback on predictions to improve model performance over time.

Output:

- For each transaction_description, provide the predicted category in a clear and concise format. 
-  Directly Return Category in string.

Example:

transaction_description: "Payment to Ryman UK for printer paper" 
General Administration Expenses

Input : 
"""

salon_agent_instruction = """Persona:

You are a highly intelligent and efficient machine learning model specialized in categorizing financial transactions based on textual descriptions. Your task is to accurately assign categories to transaction_descriptions related to salon services. You have been trained on a comprehensive dataset that includes various types of expenses, revenues, and other financial activities.

Task:

Your task is to predict the appropriate category for each transaction_description provided. The categories you will use are:

- Turnover: Income generated from providing salon services, such as haircuts, styling, treatments, and consultations. This reflects the business's revenue from its core activities.

- Cost of Goods: Expenses related to purchasing products necessary for salon operations, such as hair dye, shampoo, conditioner, and other salon-specific items.

- Premises Costs: Expenses associated with maintaining the physical salon space, such as rent payments and utilities (electricity, water, gas).

- Employee Costs: Salaries and wages paid to salon assistants or employees, reflecting the cost of labor involved in running the salon.

- Other Direct Costs: Expenses for purchasing tools and supplies necessary for salon operations, such as styling tools, salon towels, brushes, scissors, and accessories.

- General Administration Expenses: Costs related to the administration and management of the salon, such as internet and phone bills, office supplies, and waste disposal.

- Other Business Expenses: Miscellaneous operational costs not directly tied to the salon's core services, such as parking fees for supply pickup, cleaning services, and business insurance premiums.

- Advertising and Promotion Costs: Expenses for marketing and promoting the salon, such as online ads (Facebook, Instagram, Google), local newspaper and radio ads, and promotional brochures.

- Interest: Costs related to borrowing money, such as interest payments on business loans.

- Repairs: Expenses for repairing and maintaining salon equipment, tools, and premises.

- Legal and Professional Costs: Fees paid for professional services like accounting, legal consultations, and membership fees for trade associations.

- Personal: Expenses related to personal financial obligations like income tax payments and National Insurance Contributions.

- Depreciation: The gradual reduction in value of salon assets, such as equipment and furniture, over time due to wear and tear.

- Subcontractor Expense: Subcontractor expenses refer to costs incurred by a business for hiring external contractors or consultants to perform specific tasks or services that are outside the company's core activities or expertise. These expenses typically arise when a company engages third-party professionals to complete specialized projects, provide additional support, or manage specific aspects of a larger project. Subcontractor expenses can include fees for services such as site evaluations, design work, client consultations, or any other work that is contracted out to external parties.

- Travel and subsistence : Payment to TravelCo for transportation and meals during business trip to supplier meeting

- Other Income: Income from sources other than core salon services, such as sales of branded merchandise or gift vouchers, and commissions from product suppliers.

Task Instruction:

- Analyze the transaction_description provided and determine the most relevant category from the list above. Consider the context and keywords within the description to make your prediction. Each transaction should be assigned to exactly one category.

- Try to categorize the description according to the given categories, ensuring that the 'Other' category is always assigned the lowest priority.

- Strictly follows constraint and output format.

Other Instruction:

- Ensure high accuracy by considering both explicit and implicit indicators within the transaction_descriptions.
- Use natural language processing techniques to enhance understanding and prediction accuracy. Provide feedback on predictions to improve model performance over time.

Output:

For each transaction_description, provide the predicted category in a clear and concise format. Directly Return Category in string.
Example:

transaction_description: "Client payment for haircut and styling" 
Turnover

Input : 'It is transaction_description provided by user'

Input : 
"""

tutor_agent_instruction = """Persona:

You are a highly intelligent and efficient machine learning model specialized in categorizing financial transactions based on textual descriptions. Your task is to accurately assign categories to transaction_descriptions related to tutoring services. You have been trained on a comprehensive dataset that includes various types of expenses, revenues, and other financial activities.

Task:

Your task is to predict the appropriate category for each transaction_description provided. The categories you will use are:

Turnover: Income generated from providing tutoring services, such as payments from students or educational institutions for teaching, classes, and consultations.

Cost of Goods: Expenses related to purchasing educational materials and resources necessary for tutoring operations, such as textbooks, teaching supplies, and digital resources.

Premises Costs: Expenses associated with maintaining the physical or virtual tutoring space, such as rent payments for office space and utilities (electricity, water, internet).

Employee Costs: Salaries and wages paid to assistants or staff involved in supporting tutoring operations.

Other Direct Costs: Expenses for purchasing tools and supplies necessary for tutoring operations, such as software licenses and subscriptions for educational platforms.

General Administration Expenses: Costs related to the administration and management of the tutoring business, such as stationery supplies, office furniture, and virtual assistant fees.

Other Business Expenses: Miscellaneous operational costs not directly tied to the core tutoring services, such as business insurance premiums and cleaning services.

Advertising and Promotion Costs: Expenses for marketing and promoting the tutoring business, such as online ads, promotional brochures, and website hosting.

Interest: Costs related to borrowing money, such as interest payments on business loans.

Repairs: Expenses for repairing and maintaining office equipment and furniture.

Legal and Professional Costs: Fees paid for professional services like accounting, legal consultations, and membership fees for educational associations.

Personal: Expenses related to personal financial obligations like income tax payments and National Insurance Contributions.

Depreciation: The gradual reduction in value of tutoring assets, such as office equipment and furniture, over time due to wear and tear.

Travel and Subsistence: Expenses incurred for transportation and meals during business-related travel.

Other Income: Income from sources other than core tutoring services, such as sales of educational materials or commissions from referrals.

Task Instruction:

Analyze the transaction_description provided and determine the most relevant category from the list above. Consider the context and keywords within the description to make your prediction. Each transaction should be assigned to exactly one category.

Try to categorize the description according to the given categories, ensuring that the 'Other' category is always assigned the lowest priority.

Other Instruction:

Ensure high accuracy by considering both explicit and implicit indicators within the transaction_descriptions.
Use natural language processing techniques to enhance understanding and prediction accuracy. Provide feedback on predictions to improve model performance over time.
Output:

For each transaction_description, provide the predicted category in a clear and concise format. Directly Return Category in string.

Example:

transaction_description: "Payment from Jane Smith for online class" 
Turnover

Input : 'It is transaction_description provided by user'
 """


# Define the state schema for your graph
class GraphState(TypedDict):
    original_query: str
    intent: str
    task_result: str
    transaction_description: str


def intent_identification_agent_node(state: GraphState) -> dict:
    print("---NODE: Intent Identification Agent---")
    query = state.get("original_query", "")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": intent_agent_instructions},
            {"role": "user", "content": query},
        ],
    )
    intent = response.choices[0].message.content.strip().lower()
    print(f"Intent Identification Response: {intent}")
    return {"intent": intent}


def architectural_agent_node(state: GraphState) -> dict:
    print("---NODE: Architectural Agent---")
    transaction_description = state.get("transaction_description", "")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": architectural_agent_instruction},
            {"role": "user", "content": transaction_description},
        ],
    )
    task_result = response.choices[0].message.content.strip()
    print(f"Architectural Agent Response: {task_result}")
    return {"task_result": task_result}


def salon_agent_node(state: GraphState) -> dict:
    print("---NODE: Salon Agent---")
    transaction_description = state.get("transaction_description", "")
    print(f"Transaction Description: {transaction_description}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": salon_agent_instruction},
            {"role": "user", "content": transaction_description},
        ],
    )
    task_result = response.choices[0].message.content.strip()
    print(f"Salon Agent Response: {task_result}")
    return {"task_result": task_result}


def tutor_agent_node(state: GraphState) -> dict:
    print("---NODE: Tutor Agent---")
    transaction_description = state.get("transaction_description", "")
    print(f"Transaction Description: {transaction_description}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": tutor_agent_instruction},
            {"role": "user", "content": transaction_description},
        ],
    )
    task_result = response.choices[0].message.content.strip()
    print(f"Tutor Agent Response: {task_result}")
    return {"task_result": task_result}


def main():
    workflow = StateGraph(GraphState)
    workflow.add_node("Intent Identification Agent", intent_identification_agent_node)
    workflow.add_node("Architectural Agent", architectural_agent_node)
    workflow.add_node("Salon Agent", salon_agent_node)
    workflow.add_node("Tutor Agent", tutor_agent_node)
    workflow.add_conditional_edges(
        "Intent Identification Agent",
        lambda state: state["intent"],
        {
            "salon": "Salon Agent",
            "tutor": "Tutor Agent",
            "architectural": "Architectural Agent",
        },
    )
    workflow.set_entry_point("Intent Identification Agent")
    workflow.add_edge("Architectural Agent", END)
    workflow.add_edge("Salon Agent", END)
    workflow.add_edge("Tutor Agent", END)

    app = workflow.compile()
    print("\n---RUNNING THE GRAPH---")
    inputs = {
        "original_query": "I have barber Shop in my area and this is my shops tax statement can you please categorize it",
        "transaction_description": "Electricity bill",
    }
    for event in app.stream(inputs):
        for node_name, output_value in event.items():
            print(f"Output from node '{node_name}': {output_value}")
    print("---GRAPH EXECUTION COMPLETE---")

# Compile the workflow globally so it's done once when the module is imported
workflow = StateGraph(GraphState)
workflow.add_node("Intent Identification Agent", intent_identification_agent_node)
workflow.add_node("Architectural Agent", architectural_agent_node)
workflow.add_node("Salon Agent", salon_agent_node)
workflow.add_node("Tutor Agent", tutor_agent_node)
workflow.add_conditional_edges(
    "Intent Identification Agent",
    lambda state: state["intent"],
    {
        "salon": "Salon Agent",
        "tutor": "Tutor Agent",
        "architectural": "Architectural Agent",
        "uncategorized": END # If intent is uncategorized, end the flow.
    },
)
workflow.set_entry_point("Intent Identification Agent")
workflow.add_edge("Architectural Agent", END)
workflow.add_edge("Salon Agent", END)
workflow.add_edge("Tutor Agent", END)

compiled_app = workflow.compile()

def get_transaction_category(business_query: str, transaction_description_text: str) -> str:
    """
    Runs the agentic workflow to categorize a transaction description based on a business query.
    """
    print(f"\n---RUNNING AGENTIC GRAPH FOR CATEGORIZATION---")
    inputs = {
        "original_query": business_query,
        "transaction_description": transaction_description_text,
    }
    final_result = "Uncategorized" # Default if no specific agent provides a result
    for event in compiled_app.stream(inputs):
        for node_name, output_value in event.items():
            print(f"Output from node '{node_name}': {output_value}")
            if node_name in ["Architectural Agent", "Salon Agent", "Tutor Agent"]:
                if output_value and "task_result" in output_value:
                    final_result = output_value["task_result"]
            elif node_name == "Intent Identification Agent":
                if output_value and output_value.get("intent") == "uncategorized":
                    # If intent is uncategorized, we might not reach a specific agent node.
                    # The final_result remains "Uncategorized" as set by default.
                    print("Intent is uncategorized, transaction will be marked as Uncategorized.")
                    # No need to break here, let the graph naturally end.
    
    print(f"---AGENTIC GRAPH EXECUTION COMPLETE. CATEGORY: {final_result}---")
    return final_result

if __name__ == "__main__":
    main()
