import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from TargetDataSchema import ZillowDataPayload
from ScrapingZillowStatic import fetch_zillow_raw_html

# 1. Ensure API Key is accessible
os.environ["NVIDIA_API_KEY"] = "yourapikeysgoesintohere."

# 2. Initialize the Nvidia Model
# We use a solid reasoning model to parse the dense raw data
# llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct", temperature=0)
llm = ChatNVIDIA(
    model="nvidia/nemotron-3-super-120b-a12b",
    temperature=0.1,  # Low temperature forces strict adherence to pricing and housing rules
    max_completion_tokens=2048
)

# 3. Create a clean system prompt instructing the LLM exactly how to handle the data

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an expert RPA data parsing agent and a strict data validator.\n\n"
        "Your task is to analyze raw HTML card text snippets scraped from Zillow and extract "
        "all single-family house listings in Pasadena, MD.\n\n"
        "CRITICAL FILTRATION RULES:\n"
        "1. PROPERTY TYPE: Extract ONLY single-family detached homes. Strictly ignore townhouses, condos, apartments, rowhouses, or land lots.\n"
        "2. MAXIMUM PRICE CAP: Only extract listings where the price is strictly LESS THAN $500,000 (Price < $500,000).\n"
        "   - If a listing is priced at $500,000, or any higher number, you must completely DROP it from the dataset.\n"
        "   - Double-check your numerical extraction math before compiling the final JSON object array.\n\n"
        "Return the output strictly matching this JSON schema:\n{schema}"
    )),
    ("human", "Here is the scraped property cards data: {raw_data}")
])

# 4. Bind the schema structure directly to the model
structured_llm = llm.with_structured_output(ZillowDataPayload)


# 5. Build a reliable execution pipeline
class AgentExecutorPipeline:
    def __init__(self, tool, prompt, structured_llm):
        self.tool = tool
        self.chain = prompt | structured_llm

    def invoke(self, inputs: dict):
        # Step 1: Execute optimized tool
        raw_html_data = self.tool.invoke(inputs["url"])

        # Step 2: Pass clean JSON array directly to the LLM (No truncation required!)
        print("Passing isolated property block to Nvidia LLM for validation...")
        response = self.chain.invoke({
            "schema": ZillowDataPayload.schema_json(),
            "raw_data": raw_html_data
        })
        return response

# Instantiate the pipeline object so main.py can import it
agent_executor = AgentExecutorPipeline(
    tool=fetch_zillow_raw_html,
    prompt=prompt,
    structured_llm=structured_llm
)