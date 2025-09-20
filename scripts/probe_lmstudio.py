from openai import OpenAI
import os, sys, time
base = os.environ.get("OPENAI_BASE_URL","http://127.0.0.1:1234/v1")
key  = os.environ.get("OPENAI_API_KEY","lm-studio")
model= os.environ.get("MODEL","openai/gpt-oss-20b")
c = OpenAI(base_url=base, api_key=key)
ids = [m.id for m in c.models.list().data]
print(f"[probe] models: {ids[:4]}{'...' if len(ids)>4 else ''}")
t0=time.time()
r = c.chat.completions.create(model=model, messages=[{"role":"user","content":"Reply with the single word: pong"}], temperature=0, max_tokens=5)
print(f"[probe] chat: {(time.time()-t0)*1000:.1f} ms -> {r.choices[0].message.content.strip()!r}")
