import os
import subprocess
from git import Repo
from agent.generator import generate_playwright_code
from agent.runner import run_tests_in_sandbox
from agent.corrector import patch_code_with_llm


def write_files(page_code: str, test_code: str):
    os.makedirs("pages", exist_ok=True)
    os.makedirs("tests", exist_ok=True)

    with open("pages/generated_page.py", "w") as f:
        f.write(page_code)
    with open("tests/test_generated.py", "w") as f:
        f.write(test_code)


def format_code():
    subprocess.run(["black", "pages/generated_page.py", "tests/test_generated.py"])


def git_commit_clean_tests():
    repo = Repo(".")
    repo.index.add(["pages/generated_page.py", "tests/test_generated.py"])
    repo.index.commit("auto-agent: add passing playwright E2E test suite")
    print(" Successfully committed clean test files to git.")


def main(user_story: str, max_retries: int = 3):
    print(f" Parsing scenario and generating code...")
    code_dict = generate_playwright_code(user_story)

    for attempt in range(1, max_retries + 1):
        print(f" Execution Iteration {attempt}/{max_retries}...")
        write_files(code_dict["page_object_code"], code_dict["test_code"])

        success, logs = run_tests_in_sandbox()

        if success:
            print(" Execution Succeeded! Formatting code...")
            format_code()
            git_commit_clean_tests()
            return True
        else:
            print(f" Execution Failed with trace:\n{logs[:300]}...")
            if attempt < max_retries:
                print(" Triggering Self-Correction Loop...")
                code_dict = patch_code_with_llm(
                    user_story,
                    code_dict["page_object_code"],
                    code_dict["test_code"],
                    logs,
                )

    print(" Reached maximum retry limit without full self-correction.")
    return False


if __name__ == "__main__":
    scenario = "User navigates to 'https://demo.playwright.dev/todomvc', adds 'Buy Milk' to the list, and verifies 'Buy Milk' item is visible."
    main(scenario)