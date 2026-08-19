import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI()

def generate_playwright_code(user_story: str) -> dict:
    prompt = f"""
    You are an expert QA Automation Engineer specializing in Python, pytest-playwright, and Page Object Model (POM).
    Convert this Natural Language User Story into Python Playwright code:

    USER STORY:
    "{user_story}"

    REQUIREMENTS:
    1. Separate response into two parts:
       - Page Object Class (`pages/generated_page.py`)
       - Test File (`tests/test_generated.py`) using `pytest` fixtures like `page: Page`.
    2. Use `playwright.sync_api` locators (e.g., `get_by_role`, `get_by_label`, `locator`).
    3. Output pure JSON matching this structure:
    {{
       "page_object_code": "...",
       "test_code": "..."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    import json

    return json.loads(response.choices[0].message.content)