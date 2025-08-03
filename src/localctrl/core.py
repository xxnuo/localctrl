import asyncio
import shlex

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from localctrl.logger import logger
from localctrl.user import Role, User, get_user

coreRouter = APIRouter()


class ExecRequest(BaseModel):
    command: str


@coreRouter.post("/exec/py")
async def py_exec(request: ExecRequest, user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    async def execute_command():
        try:
            logger.info(f"Executing Python command: {request.command}")
            process = await asyncio.create_subprocess_exec(
                "python",
                "-c",
                request.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async def read_stream(stream):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    yield line.decode("utf-8")

            async for line in read_stream(process.stdout):
                yield line

            # 也读取stderr的输出
            async for line in read_stream(process.stderr):
                yield line

            await process.wait()
            logger.info(
                f"Python command execution completed with return code: {process.returncode}"
            )
        except Exception as e:
            logger.error(f"Error executing Python command: {str(e)}")
            yield f"Error: {str(e)}\n"

    return StreamingResponse(execute_command(), media_type="text/plain")


@coreRouter.post("/exec")
async def exec(request: ExecRequest, user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    # 处理命令，检查是否包含危险命令
    danger_commands = ["rm", "mv", "cp", "ln", "chmod", "chown", "chgrp"]

    cmd_parts = request.command.split("&&")
    for part in cmd_parts:
        part = part.strip()
        if part and part.split(" ")[0].lower() in danger_commands:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Dangerous command"
            )

    async def execute_command():
        try:
            logger.info(f"Executing command: {request.command}")
            process = await asyncio.create_subprocess_exec(
                *shlex.split(request.command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async def read_stream(stream):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    yield line.decode("utf-8")

            async for line in read_stream(process.stdout):
                yield line

            await process.wait()
            logger.info(
                f"Command execution completed with return code: {process.returncode}"
            )
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            yield f"Error: {str(e)}\n"

    return StreamingResponse(execute_command(), media_type="text/plain")
