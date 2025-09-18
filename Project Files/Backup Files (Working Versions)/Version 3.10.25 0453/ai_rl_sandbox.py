import os
import subprocess

class AIRLSandbox:
    def __init__(self, ai_file="C:/AI_Project/ai_core.py"):
        self.ai_file = ai_file

    def test_modification(self, modification):
        """Runs AI modifications in a safe environment before applying them."""
        sandbox_file = "C:/AI_Project/sandbox/ai_core_sandbox.py"
        
        if not os.path.exists("C:/AI_Project/sandbox/"):
            os.makedirs("C:/AI_Project/sandbox/")

        # ✅ Copy AI Core Code & Apply Test Modification
        with open(self.ai_file, "r", encoding="utf-8") as original, open(sandbox_file, "w", encoding="utf-8") as sandbox:
            for line in original:
                sandbox.write(line)
            sandbox.write("\n" + modification)

        # ✅ Test Sandbox Code Execution
        try:
            result = subprocess.run(["python", sandbox_file], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ AI Modification Passed Sandbox Test.")
                return True
            else:
                print("🚨 AI Modification Failed: Sandbox Error.")
                return False

        except Exception as e:
            print(f"🚨 AI Sandbox Execution Failed: {str(e)}")
            return False

# ✅ Initialize AI Reinforcement Learning Sandbox
ai_rl_sandbox = AIRLSandbox()
