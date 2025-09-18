def run(code: str):
    # Extremely restricted placeholder
    local = {}
    exec(code, {}, local)
    return local
