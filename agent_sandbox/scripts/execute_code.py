import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from microsandbox import Sandbox

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.modules import execute_code, set_dataframe

load_dotenv()

LOAD_DF = "import pandas as pd; df = pd.read_pickle('/data/df.pkl')\n"

async def main() -> None:
    async with await Sandbox.create(
        "06-execute-code",
        image="python",
        memory=1024,
        replace=True
    ) as sandbox:
        await sandbox.shell("pip install -q pandas", timeout=300)

        with open("data/sample.csv", "rb") as fi:
            await set_dataframe(sandbox=sandbox, file_object=fi)

        data_thread = await execute_code(
            process_id="06_execue_code",
            thread_id=0,
            sandbox=sandbox,
            code=LOAD_DF + "print(df.shape)",
        )
        print(data_thread.model_dump_json(indent=4))

if __name__ == "__main__":
    asyncio.run(main())