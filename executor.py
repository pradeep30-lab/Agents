import httpx
import asyncio
import xml.etree.ElementTree as ET
from schemas import TestCase


async def execute_test(client: httpx.AsyncClient, test_case: TestCase) -> dict:
    try:
        res = await client.request(
            method=test_case.method,
            url=test_case.endpoint,
            headers=test_case.headers,
            params=test_case.query_params,
            json=test_case.body
        )
        status = res.status_code
        # Failure logic: status code not expected OR unhandled server error (500)
        passed = (status in test_case.expected_status_codes) and (status != 500)

        return {
            "test_id": test_case.test_id,
            "passed": passed,
            "status": status,
            "expected": test_case.expected_status_codes,
            "response": res.text[:200]
        }
    except Exception as e:
        return {"test_id": test_case.test_id, "passed": False, "error": str(e)}


async def run_suite(base_url: str, test_cases: list[TestCase]):
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        tasks = [execute_test(client, tc) for tc in test_cases]
        return await asyncio.gather(*tasks)


def export_junit_xml(results: list[dict], filename="results.xml"):
    suite = ET.Element("testsuite", name="OpenAPI Agent Suite", tests=str(len(results)))
    failures = 0
    for r in results:
        tc = ET.SubElement(suite, "testcase", name=r["test_id"])
        if not r["passed"]:
            failures += 1
            fail = ET.SubElement(tc, "failure", message="Assertion Failed")
            fail.text = f"Got {r.get('status')}, expected {r.get('expected')}. Body: {r.get('response')}"
    suite.set("failures", str(failures))
    ET.ElementTree(suite).write(filename, encoding="utf-8", xml_declaration=True)