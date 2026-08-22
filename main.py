import asyncio
from parser import parse_spec
from generator import generate_tests_for_endpoint
from executor import run_suite, export_junit_xml


async def main():
    spec_path = "openapi.json"
    base_url = "http://staging-api.example.com"

    endpoints = parse_spec(spec_path)
    all_tests = []

    print(f"Parsed {len(endpoints)} endpoints. Generating test vectors...")
    for ep in endpoints:
        suite = generate_tests_for_endpoint(ep)
        all_tests.extend(suite.test_cases)

    print(f"Executing {len(all_tests)} test cases against {base_url}...")
    results = await run_suite(base_url, all_tests)

    export_junit_xml(results)
    print("Execution complete. Exported report to results.xml.")


if __name__ == "__main__":
    asyncio.run(main())