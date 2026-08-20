import asyncio
import inspect
import json
import os
from datetime import datetime
from typing import Any, Callable, Coroutine
from pydantic import BaseModel, Field
import openai
import instructor
from playwright.async_api import async_playwright, expect, Page
import pytest

# Initialize instructor client for constrained JSON outputs
client = instructor.from_openai(
    openai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
)


# --- 1. Pydantic Model for Repair Output ---
class SelectorRepairResponse(BaseModel):
    repaired_selector: str = Field(
        description="A valid Playwright locator string (e.g., 'input[name=\"where\"]', 'text=\"Search\"', 'button:has-text(\"Submit\")')."
    )
    confidence_score: float = Field(
        description="Confidence score between 0.0 and 1.0."
    )
    reasoning: str = Field(
        description="Brief explanation of why this element matches the user intention."
    )


# --- 2. Construct Repair Agent ---
# --- Updated Repair Agent ---
async def repair_agent(
        broken_locator: str,
        user_intention: str,
        aria_snapshot: str
) -> SelectorRepairResponse:
    prompt = f"""
    You are an automated Playwright Selector Repair Agent.

    - Broken Locator: {broken_locator}
    - User Target Intention: {user_intention}
    - Page ARIA Snapshot / Accessibility Tree:
    {aria_snapshot}

    Rules:
    1. Identify the input element that fulfills the user intention.
    2. Return a valid Playwright page.locator() target string. Prefer precise CSS selectors (e.g. "input[data-testid='structured-search-input-field-query']", "input[name='query']", "#bigsearch-default-location-input").
    3. Avoid using role-based pseudo-selectors like 'searchbox[aria-label=...]' if the element might be a trigger wrapper.
    """

    return await client.chat.completions.create(
        model="gpt-4o",
        response_model=SelectorRepairResponse,
        messages=[
            {"role": "system", "content": "You repair broken UI test automation selectors."},
            {"role": "user", "content": prompt}
        ]
    )

# --- 3. Healing Logger Helper ---
def log_healing_event(broken: str, repaired: str, confidence: float, reasoning: str,
                      file_path: str = "healing_log.json"):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "broken_selector": broken,
        "repaired_selector": repaired,
        "confidence_score": confidence,
        "reasoning": reasoning
    }

    logs = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []

    logs.append(log_entry)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

    print(f" -> Successfully appended fix to '{file_path}'")



# --- Updated Execution Interceptor ---
async def execution_interceptor(
    page: Page, method_name: str, args: tuple, kwargs: dict, error: Exception, locator_string: str
):
    print(f"\n[INTERCEPTOR TRIGGERED]")
    print(f" -> Action Failed: {method_name}")
    print(f" -> Broken Locator: {locator_string}")

    try:
        aria_tree = await page.aria_snapshot()

        action_input = args[0] if args else kwargs.get("value", "")
        user_intention = f"Perform '{method_name}' with value '{action_input}' on target field"

        print(" -> Requesting selector repair from Repair Agent LLM...")
        repair_result = await repair_agent(
            broken_locator=locator_string,
            user_intention=user_intention,
            aria_snapshot=aria_tree
        )

        repaired_sel = repair_result.repaired_selector
        print(f" -> Repaired Selector Generated: {repaired_sel} (Confidence: {repair_result.confidence_score})")

        repaired_locator = page.locator(repaired_sel)

        # Handle UI overlay/collapsed states: click to activate if doing a fill operation
        if method_name == "fill":
            try:
                print(" -> Pre-clicking element to handle popovers/overlays...")
                await repaired_locator.click(timeout=3000)
            except Exception:
                pass  # Proceed directly if click isn't required

        action_method = getattr(repaired_locator, method_name, None)

        if not callable(action_method):
            raise AttributeError(f"Locator object has no action method '{method_name}'")

        # Strip strict timeouts inherited from failed test attempt
        retry_kwargs = kwargs.copy()
        retry_kwargs.pop("timeout", None)

        print(f" -> Re-attempting action '{method_name}' with repaired selector...")
        await action_method(*args, **retry_kwargs)
        print(" -> Action executed successfully with repaired selector!")

        log_healing_event(
            broken=locator_string,
            repaired=repaired_sel,
            confidence=repair_result.confidence_score,
            reasoning=repair_result.reasoning
        )

    except Exception as interceptor_err:
        print(f" -> Repair & Re-injection failed: {interceptor_err}")

# --- 5. Middleware Wrapper ---
class PlaywrightActionMiddleware:
    def __init__(self, target: Any, interceptor: Callable[..., Coroutine], raw_page: Page, locator_str: str = ""):
        self._target = target
        self._interceptor = interceptor
        self._raw_page = raw_page
        self._locator_str = locator_str

    def __getattr__(self, name: str):
        attr = getattr(self._target, name)

        if not callable(attr):
            return attr

        def wrapper(*args, **kwargs):
            res = attr(*args, **kwargs)

            if asyncio.iscoroutine(res) or inspect.isawaitable(res):
                async def async_runner():
                    try:
                        return await res
                    except Exception as e:
                        await self._interceptor(
                            self._raw_page, name, args, kwargs, e, self._locator_str
                        )
                        return None

                return async_runner()

            if hasattr(res, "click") or hasattr(res, "fill"):
                current_loc = f"{self._locator_str}.{name}({', '.join(map(repr, args))})" if self._locator_str else f"{name}({', '.join(map(repr, args))})"
                return PlaywrightActionMiddleware(res, self._interceptor, self._raw_page, current_loc)

            return res

        return wrapper


# --- 6. Test Case ---
@pytest.mark.asyncio
async def test_verify_airbnb_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        raw_page = await browser.new_page()

        mypage = PlaywrightActionMiddleware(raw_page, execution_interceptor, raw_page)

        await mypage.goto("https://www.airbnb.com/")
        await expect(raw_page).to_have_url("https://www.airbnb.com/")

        # Intentional failure: triggers interceptor, repairs selector, re-injects fill(), and logs output
        await mypage.get_by_test_id("structured-search-input-field").fill("Fremont", timeout=3000)

        await browser.close()