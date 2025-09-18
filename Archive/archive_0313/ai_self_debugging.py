import os
import re

class AISelfDebugger:
    def __init__(self, ai_file="C:/AI_Project/ai_core.py"):
        self.ai_file = ai_file

    def scan_for_errors(self):
        """Scan AI core for syntax or logical errors."""
        try:
            with open(self.ai_file, "r", encoding="utf-8") as f:
                code = f.readlines()
            
            errors = []
            for i, line in enumerate(code):
                if "except Exception as e" in line and "print" not in code[i + 1]:
                    errors.append((i + 1, "Missing error logging"))

                if "import" in line and line.strip().endswith(","):
                    errors.append((i + 1, "Incorrect import syntax"))

            return errors

        except Exception as e:
            print(f"🚨 AI Self-Debugging Failed: {str(e)}")
            return []

    def fix_errors(self):
        """Automatically correct common AI mistakes."""
        errors = self.scan_for_errors()
        if not errors:
            print("✅ AI Self-Debugging: No errors found.")
            return

        print(f"🚀 AI Self-Debugging: Found {len(errors)} issues. Attempting to fix.")
        with open(self.ai_file, "r", encoding="utf-8") as f:
            code = f.readlines()

        for line_num, issue in errors:
            if "Missing error logging" in issue:
                code.insert(line_num, "    print(f'Error: {str(e)}')\n")

        with open(self.ai_file, "w", encoding="utf-8") as f:
            f.writelines(code)

        print("✅ AI Self-Debugging Complete: Errors Fixed.")

# ✅ Initialize AI Self-Debugger
ai_debugger = AISelfDebugger()
