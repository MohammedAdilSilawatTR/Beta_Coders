from typing import TypedDict, List, Dict # Added List, Dict
from langgraph.graph import StateGraph, END
from openai import OpenAI
import os
import json # Added json
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
Only return a single word: "Salon", "Tutor", "Architectural", or "Uncategorized".

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

Input:
["Payment to Ryman UK for printer paper", "Invoice for CAD software subscription"]

Output:
{
  "Payment to Ryman UK for printer paper": "General Administration Expenses",
  "Invoice for CAD software subscription": "General Administration Expenses"
}

Task Instruction:
- Analyze the list of transaction_descriptions provided and determine the most relevant category for each from the list above.
- Return a single JSON object where each key is one of the transaction descriptions from the input list, and its value is the predicted category string.
- Ensure the output is a valid JSON object. Do not add any explanatory text before or after the JSON object.

Input: (This will be a JSON string list of transaction descriptions)
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

Input:
["Client payment for haircut and styling", "Purchase of L'Oreal hair dye"]

Output:
{
  "Client payment for haircut and styling": "Turnover",
  "Purchase of L'Oreal hair dye": "Cost of Goods"
}

Task Instruction:
- Analyze the list of transaction_descriptions provided and determine the most relevant category for each from the list above.
- Return a single JSON object where each key is one of the transaction descriptions from the input list, and its value is the predicted category string.
- Ensure the output is a valid JSON object. Do not add any explanatory text before or after the JSON object.

Input: (This will be a JSON string list of transaction descriptions)
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

Analyze the transaction_descriptions provided and determine the most relevant categories from the list above. Consider the context and keywords within the description to make your prediction. Each transaction should be assigned to exactly one category.

Try to categorize the descriptions according to the given categories, ensuring that the 'Other' category is always assigned the lowest priority.

Other Instruction:

Ensure high accuracy by considering both explicit and implicit indicators within the transaction_descriptions.
Use natural language processing techniques to enhance understanding and prediction accuracy. Provide feedback on predictions to improve model performance over time.
Output:

For each transaction_description, provide the predicted category in a clear and concise format. Directly Return json reply with key as description and value as category.

Example:

Input:
["Payment from Jane Smith for online class", "Subscription to Zoom for teaching"]

Output:
{
  "Payment from Jane Smith for online class": "Turnover",
  "Subscription to Zoom for teaching": "Other Direct Costs"
}

Task Instruction:
- Analyze the list of transaction_descriptions provided and determine the most relevant category for each from the list above.
- Return a single JSON object where each key is one of ઉthe transaction descriptions from the input list, and its value is the predicted category string.
- Ensure the output is a valid JSON object. Do not add any explanatory text before or after the JSON object.

Input: (This will be a JSON string list of transaction descriptions)
"""


# Define the state schema for your graph
class GraphState(TypedDict):
    original_query: str  # Business description
    intent: str          # Identified business intent
    transaction_descriptions: List[str]  # List of transaction descriptions to categorize
    categorization_results: Dict[str, str] # Map of {description: category}


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
    descriptions = state.get("transaction_descriptions", [])
    if not descriptions:
        print("Architectural Agent: No descriptions to categorize.")
        return {"categorization_results": {}}
    
    user_content = json.dumps(descriptions)
    print(f"Architectural Agent sending to LLM: {user_content}")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": architectural_agent_instruction},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content.strip()
        print(f"Architectural Agent LLM raw response: {response_content}")
        categorization_results = json.loads(response_content)
        print(f"Architectural Agent Parsed Response: {categorization_results}")
        return {"categorization_results": categorization_results}
    except Exception as e:
        print(f"Error in Architectural Agent: {e}")
        # Fallback: mark all as "Error in Categorization" for this agent
        return {"categorization_results": {desc: "Error in Categorization" for desc in descriptions}}


def salon_agent_node(state: GraphState) -> dict:
    print("---NODE: Salon Agent---")
    descriptions = state.get("transaction_descriptions", [])
    if not descriptions:
        print("Salon Agent: No descriptions to categorize.")
        return {"categorization_results": {}}

    user_content = json.dumps(descriptions)
    print(f"Salon Agent sending to LLM: {user_content}")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": salon_agent_instruction},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content.strip()
        print(f"Salon Agent LLM raw response: {response_content}")
        categorization_results = json.loads(response_content)
        print(f"Salon Agent Parsed Response: {categorization_results}")
        return {"categorization_results": categorization_results}
    except Exception as e:
        print(f"Error in Salon Agent: {e}")
        return {"categorization_results": {desc: "Error in Categorization" for desc in descriptions}}


def tutor_agent_node(state: GraphState) -> dict:
    print("---NODE: Tutor Agent---")
    descriptions = state.get("transaction_descriptions", [])
    if not descriptions:
        print("Tutor Agent: No descriptions to categorize.")
        return {"categorization_results": {}}

    user_content = json.dumps(descriptions)
    print(f"Tutor Agent sending to LLM: {user_content}")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": tutor_agent_instruction},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content.strip()
        print(f"Tutor Agent LLM raw response: {response_content}")
        categorization_results = json.loads(response_content)
        print(f"Tutor Agent Parsed Response: {categorization_results}")
        return {"categorization_results": categorization_results}
    except Exception as e:
        print(f"Error in Tutor Agent: {e}")
        return {"categorization_results": {desc: "Error in Categorization" for desc in descriptions}}


# Compile the workflow globally so it's done once when the module is imported
graph_builder = StateGraph(GraphState) 
graph_builder.add_node("Intent Identification Agent", intent_identification_agent_node)
graph_builder.add_node("Architectural Agent", architectural_agent_node)
graph_builder.add_node("Salon Agent", salon_agent_node)
graph_builder.add_node("Tutor Agent", tutor_agent_node)
graph_builder.add_conditional_edges(
    "Intent Identification Agent",
    lambda state: state.get("intent", "").lower(), # Ensure intent is lowercased and handle if None
    {
        "salon": "Salon Agent",
        "tutor": "Tutor Agent",
        "architectural": "Architectural Agent",
        "uncategorized": END # If intent is uncategorized, end the flow.
    },
)
graph_builder.set_entry_point("Intent Identification Agent")
graph_builder.add_edge("Architectural Agent", END)
graph_builder.add_edge("Salon Agent", END)
graph_builder.add_edge("Tutor Agent", END)

compiled_app = graph_builder.compile()

def get_batch_categories(business_query: str, descriptions_list: List[str]) -> Dict[str, str]:
    """
    Runs the agentic workflow to categorize a batch of transaction descriptions based on a business query.
    Returns a dictionary mapping each description to its category.
    """
    print(f"\n---RUNNING AGENTIC GRAPH FOR BATCH CATEGORIZATION---")
    if not descriptions_list:
        print("No descriptions provided for batch categorization.")
        return {}

    inputs = {
        "original_query": business_query,
        "transaction_descriptions": descriptions_list,
        "categorization_results": {} # Initialize
    }
    
    final_category_map: Dict[str, str] = {}

    for event in compiled_app.stream(inputs):
        for node_name, output_value in event.items():
            print(f"Output from node '{node_name}': {output_value}")
            if node_name == "Intent Identification Agent":
                current_intent = output_value.get("intent", "").lower()
                if current_intent == "uncategorized":
                    print("Intent is uncategorized. All descriptions in batch marked as Uncategorized.")
                    final_category_map = {desc: "Uncategorized" for desc in descriptions_list}
                    # The graph will end due to the conditional edge.
            elif node_name in ["Architectural Agent", "Salon Agent", "Tutor Agent"]:
                if output_value and "categorization_results" in output_value:
                    # Merge results, prioritizing agent's output
                    # This handles cases where some descriptions might not be in the agent's map
                    # or if the agent returns an incomplete map.
                    agent_map = output_value["categorization_results"]
                    current_batch_map = {desc: "Uncategorized" for desc in descriptions_list} # Default all
                    current_batch_map.update(agent_map) # Update with agent's results
                    final_category_map = current_batch_map
            
    # If the graph ended due to 'uncategorized' intent, final_category_map is already set.
    # If it went through an agent, final_category_map is set by the agent's output.
    # If for some reason final_category_map is still empty (e.g., unexpected graph flow or error before agent node),
    # ensure all descriptions get a default category.
    if not final_category_map and descriptions_list:
         final_category_map = {desc: "Uncategorized" for desc in descriptions_list}
    elif descriptions_list: # Ensure all descriptions from input list are covered
        for desc_key in descriptions_list:
            if desc_key not in final_category_map:
                final_category_map[desc_key] = "Uncategorized" # Default for any missing keys

    print(f"---AGENTIC GRAPH EXECUTION COMPLETE. CATEGORY MAP: {final_category_map}---")
    return final_category_map

if __name__ == "__main__":
    # Test the batch categorization
    test_business_query_salon = "This is a hair salon."
    test_descriptions_salon = [
        "Payment for shampoo and conditioner supplies",
        "Client payment for hair coloring service",
        "Rent for salon premises",
        "Facebook ad campaign for new styles",
        "This is an unknown item"
    ]
    
    results_salon = get_batch_categories(test_business_query_salon, test_descriptions_salon)
    print("\n---FINAL BATCH SALON CATEGORIZATION RESULTS (main test)---")
    for desc, category in results_salon.items():
        print(f"Description: '{desc}' -> Category: '{category}'")

    test_business_query_arch = "Architectural design firm"
    test_descriptions_arch = ["CAD software license renewal", "Client consultation fee for new building project", "Travel to site visit"]
    results_arch = get_batch_categories(test_business_query_arch, test_descriptions_arch)
    print("\n---FINAL BATCH ARCH CATEGORIZATION RESULTS (main test)---")
    for desc, category in results_arch.items():
        print(f"Description: '{desc}' -> Category: '{category}'")

    test_business_query_uncat = "A general store that sells various items."
    test_descriptions_uncat = ["Purchase of stock for shelves", "Sale of goods to customer", "Utility bill for the store"]
    results_uncat = get_batch_categories(test_business_query_uncat, test_descriptions_uncat)
    print("\n---FINAL BATCH UNCAT CATEGORIZATION RESULTS (main test)---")
    for desc, category in results_uncat.items():
        print(f"Description: '{desc}' -> Category: '{category}'")

    test_business_query_tutor = "Online math tutoring services"
    test_descriptions_tutor = ["Payment from student John Doe", "Subscription for online whiteboard tool", "Advertisement on education portal"]
    results_tutor = get_batch_categories(test_business_query_tutor, test_descriptions_tutor)
    print("\n---FINAL BATCH TUTOR CATEGORIZATION RESULTS (main test)---")
    for desc, category in results_tutor.items():
        print(f"Description: '{desc}' -> Category: '{category}'")
