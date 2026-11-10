from loguru import logger
from microsandbox import Sandbox

from src.models import DataThread

async def execute_code(
    sandbox: Sandbox,
    process_id: str,
    thread_id: int,
    code: str,
    user_request: str | None = None,
    timeout: float = 1200,
) -> DataThread:
    execution = await sandbox.exec("python", ["-c", code], timeout=timeout)
    logger.debug(f"{execution=}")
    return DataThread(
        id=thread_id,
        process_id=process_id,
        thread_id=thread_id,
        user_request=user_request,
        code=code,
        error=None if execution.success else execution.stderr_text.strip(),
        stderr=execution.stderr_text.strip(),
        stdout=execution.stdout_text.strip(),
        results=[]
    )