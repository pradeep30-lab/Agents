import json
import os
import re
import sys

LOG_FILE = "healing_log.json"
POM_DIR = "pages"  # Path to your Page Object Models directory (or root directory)


def apply_selector_patches():
    if not os.path.exists(LOG_FILE):
        print(f"No {LOG_FILE} found. Skipping POM patching.")
        return False

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            print(f"Invalid JSON in {LOG_FILE}.")
            return False

    if not logs:
        print("Healing log is empty.")
        return False

    patched_any = False

    for entry in logs:
        broken = entry.get("broken_selector")
        repaired = entry.get("repaired_selector")

        if not broken or not repaired:
            continue

        print(f"\nProcessing fix: '{broken}' -> '{repaired}'")

        # Extract the inner selector string if broken contains call syntax (e.g., get_by_test_id("invalid-id"))
        broken_match = re.search(r'["\']([^"\']+)["\']', broken)
        broken_str = broken_match.group(1) if broken_match else broken

        # Walk through POM files
        for root, _, files in os.walk(POM_DIR):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    if broken_str in content:
                        updated_content = content.replace(broken_str, repaired)
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(updated_content)

                        print(f" -> Patched '{broken_str}' with '{repaired}' in {filepath}")
                        patched_any = True

    return patched_any


if __name__ == "__main__":
    has_patches = apply_selector_patches()
    sys.exit(0 if has_patches else 1)