from agent.generator import client


def patch_code_with_llm(
    user_story: str,
    page_code: str,
    test_code: str,
    error_trace: str,
) -> dict:
    prompt = f"""
    The generated Playwright test failed. Fix the syntax, locator, or assertion error.

    ORIGINAL USER STORY: {user_story}

    CURRENT PAGE OBJECT CODE:
    {page_code}

    CURRENT TEST CODE:
    {test_code}

    EXECUTION ERROR TRACEBACK:
    {error_trace}

    Return the updated fixed JSON:
    {{
       "page_object_code": "...",
       "test_code": "..."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )

    import json

    return json.loads(response.choices[0].message.content)