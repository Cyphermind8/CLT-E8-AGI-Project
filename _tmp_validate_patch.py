from src.tools.patch_schema import validate_patch
def check(payload): print(validate_patch(payload))
tests = [
    {'type':'patch','intent':'add_guard','scope':{'file':'ai_core.py'},'edits':[{'op':'replace','loc':{'function':'x'},'content':'`python\n    def x():\n        return 1\n`'}],'constraints':{'max_lines_changed':20}},
    {'type':'patch','intent':'add_guard','scope':{'file':'ai_core.py'},'edits':[{'op':'replace','loc':{'function':'x'},'content':'python\n    def x():\n        return 1\n'}],'constraints':{'max_lines_changed':20}},
    {'type':'patch','intent':'add_guard','scope':{'file':'ai_core.py'},'edits':[{'op':'replace','loc':{'function':'x'},'content':'~~~python\n\tdef x():\n\t\treturn 1\n~~~'}],'constraints':{'max_lines_changed':20}},
    {'type':'patch','intent':'add_guard','scope':{'file':'ai_core.py'},'edits':[{'op':'replace','loc':{'function':'x'},'content':'    def x():\n        return 1\n'}],'constraints':{'max_lines_changed':20}},
]
for p in tests: check(p)
