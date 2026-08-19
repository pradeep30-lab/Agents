import subprocess


def run_tests_in_sandbox() -> tuple[bool, str]:
    """Runs generated tests via pytest inside Docker or local sandbox."""
    try:
        result = subprocess.run(
            ["pytest", "tests/test_generated.py", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        is_success = result.returncode == 0
        output = result.stdout + "\n" + result.stderr
        return is_success, output
    except Exception as e:
        return False, str(e)