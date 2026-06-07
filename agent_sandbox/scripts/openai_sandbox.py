import os
import re
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from microsandbox import Sandbox

# load_dotenv(dotenv_path="../.env")
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

async def run_in_sandbox(code: str) -> str:
    sandbox = await Sandbox.create(
        "agent-sandbox",
        image="python",
        cpus=1,
        memory=512,
        replace=True
    )
    await sandbox.fs.write("/tmp/script.py", code.encode())
    output = await sandbox.exec("python3", ["/tmp/script.py"])
    await sandbox.stop_and_wait()
    
    print(f"stderr: {output.stderr_text}")  # デバッグ用
    return output.stdout_text

async def main():
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user",
             "content": """
             フィボナッチ数列を10個出力するPythonコードを書いて。
             このときコードのみを返してください。
             """}
        ]   
    )
    raw = response.choices[0].message.content
    code = extract_code(raw)
    print(f"生成されたコード:\n{code}\n")

    result = await run_in_sandbox(code)
    print(f"実行結果:\n{result}")

asyncio.run(main())