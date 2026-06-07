import asyncio
from microsandbox import Sandbox

async def main():
    sandbox = await Sandbox.create(
        "test-sandbox",
        image="python",
        cpus=1,
        memory=512,
        replace=True
    )

    output = await sandbox.exec(
        "python3", ["-c", "print('Hello from microVM')"]
    )

    print(output.stderr_text)
    await sandbox.stop_and_wait()

asyncio.run(main())