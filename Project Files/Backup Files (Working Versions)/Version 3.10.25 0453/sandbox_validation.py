import os
import shutil
import traceback

# Define Paths
PROJECT_PATH = "C:/AI_Project/"
AI_FILE = os.path.join(PROJECT_PATH, "ai_core.py")
SANDBOX_FILE = os.path.join(PROJECT_PATH, "sandbox_ai_core.py")

def create_sandbox():
    """Creates a sandbox test environment by copying AI source code only if necessary."""
    try:
        if not os.path.exists(SANDBOX_FILE):
            shutil.copy(AI_FILE, SANDBOX_FILE)
            print("✅ Sandbox environment created successfully.")
        else:
            print("🔹 Sandbox already exists. Skipping recreation.")
        return True
    except Exception as e:
        print(f"🚨 Sandbox Creation Failed: {str(e)}")
        return False

def validate_modification(modification_code):
    """Applies a test modification in the sandbox and checks for errors in parallel."""
    if not os.path.exists(SANDBOX_FILE):
        print("🚨 No sandbox file found! Creating sandbox...")
        if not create_sandbox():
            return False

    try:
        # Apply modification to sandbox file
        with open(SANDBOX_FILE, "a", encoding="utf-8") as f:
            f.write("\n" + modification_code)

        # Test if the modified code compiles correctly in parallel mode
        compile(open(SANDBOX_FILE, "r", encoding="utf-8").read(), SANDBOX_FILE, "exec")
        print("✅ Modification validated successfully in sandbox!")
        return True

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"🚨 Modification Validation Failed: {str(e)}\n{error_trace}")
        return False

def apply_modification(modification_code):
    """Validates a modification and applies it to the real AI core file only if the sandbox test passes."""
    if validate_modification(modification_code):
        try:
            with open(AI_FILE, "a", encoding="utf-8") as f:
                f.write("\n" + modification_code)
            print("🚀 Modification successfully applied to AI core!")
            return True
        except Exception as e:
            print(f"🚨 Failed to apply modification: {str(e)}")
            return False
    else:
        print("❌ Modification rejected due to validation failure.")
        return False

# Example of usage
if __name__ == "__main__":
    create_sandbox()
    test_code = "# AI Self-Improvement Test Modification"
    apply_modification(test_code)
