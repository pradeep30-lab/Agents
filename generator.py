from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from schemas import EndpointTestSuite
from dotenv import load_dotenv
load_dotenv()


SYSTEM_PROMPT = """You are an API contract and security testing agent.
For the given OpenAPI operation, generate exactly 3 classes of test cases:
1. HAPPY_PATH: Valid inputs adhering strictly to types and constraints. Expected: 200/201/204.
2. BOUNDARY: Min/max length violations, nulls on required fields, type mismatches. Expected: 400/422.
3. SECURITY_ADVERSARIAL: Malformed payloads, SQL/XSS mutation strings, missing tokens. Expected: 400/401/403/422.

Never accept an unhandled 500 error as expected behavior."""


def generate_tests_for_endpoint(endpoint_data: dict) -> EndpointTestSuite:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    structured_llm = llm.with_structured_output(EndpointTestSuite, strict=False)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Generate test suite for endpoint:\n{endpoint_json}")
    ])

    chain = prompt | structured_llm
    return chain.invoke({"endpoint_json": str(endpoint_data)})