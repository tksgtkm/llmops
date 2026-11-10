import posixpath
import typing
from microsandbox import Sandbox, ExecOutput

async def set_dataframe(
    sandbox: Sandbox,
    file_object: typing.BinaryIO,
    timeout: float=1200,
    remote_data_path: str = "/data/sample.csv",
    remote_df_path: str = "/data/df.pkl",
) -> ExecOutput:
    parent = posixpath.dirname(remote_data_path)
    if not await sandbox.fs.exists(parent):
        await sandbox.fs.mkdir(parent)
    await sandbox.fs.write(remote_data_path, file_object.read())
    code = (
        "import pandas as pd; "
        f"df = pd.read_csv({remote_data_path!r}); "
        f"df.to_pickle({remote_df_path!r})"
    )
    return await sandbox.exec("python", ["-c", code], timeout=timeout)