import sys

import pyautogui
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from localctrl.logger import logger
from localctrl.user import Role, User, get_user

mediaRouter = APIRouter()


@mediaRouter.post("/mute")
async def mute(user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    try:
        # 使用pyautogui执行系统静音命令
        if sys.platform == "darwin":  # macOS
            pyautogui.keyDown("fn")
            pyautogui.keyDown("f9")
            pyautogui.keyUp("f9")
            pyautogui.keyUp("fn")  # macOS 静音键
        elif sys.platform == "win32":  # Windows
            pyautogui.press("volumemute")  # Windows 静音键
        elif sys.platform == "linux":  # Linux
            pyautogui.press("volumemute")  # Linux 静音键
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
            )

        logger.info("System muted successfully")
        return {"status": "success", "message": "System muted"}
    except Exception as e:
        logger.error(f"Error muting system: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}"
        )


@mediaRouter.post("/unmute")
async def unmute(user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    try:
        # 使用pyautogui执行系统取消静音命令
        if sys.platform == "darwin":  # macOS
            pyautogui.keyDown("fn")
            pyautogui.keyDown("f9")
            pyautogui.keyUp("f9")
            pyautogui.keyUp("fn")  # macOS 静音键（再次按下取消静音）
        elif sys.platform == "win32":  # Windows
            pyautogui.press("volumemute")  # Windows 静音键（再次按下取消静音）
        elif sys.platform == "linux":  # Linux
            pyautogui.press("volumemute")  # Linux 静音键（再次按下取消静音）
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
            )

        logger.info("System unmuted successfully")
        return {"status": "success", "message": "System unmuted"}
    except Exception as e:
        logger.error(f"Error unmuting system: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}"
        )


class VolumeRequest(BaseModel):
    level: int  # 音量级别 (0-100)


@mediaRouter.post("/volume")
async def set_volume(volume_req: VolumeRequest, user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    # 验证音量级别
    if volume_req.level < 0 or volume_req.level > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Volume level must be between 0 and 100",
        )

    try:
        # 使用pyautogui调整音量
        # 先将音量调至最低
        if sys.platform == "darwin":  # macOS
            # 先将音量调至最低
            for _ in range(16):  # 确保音量降至最低
                pyautogui.keyDown("fn")
                pyautogui.keyDown("f10")
                pyautogui.keyUp("f10")
                pyautogui.keyUp("fn")  # 音量减

            # 然后根据请求的音量级别调整
            steps = int(volume_req.level / 100 * 16)  # macOS大约有16个音量级别
            for _ in range(steps):
                pyautogui.keyDown("fn")
                pyautogui.keyDown("f11")
                pyautogui.keyUp("f11")
                pyautogui.keyUp("fn")  # 音量加
        elif sys.platform == "win32":  # Windows
            # 先将音量调至最低
            for _ in range(50):  # 确保音量降至最低
                pyautogui.press("volumedown")

            # 然后根据请求的音量级别调整
            steps = int(volume_req.level / 100 * 50)  # Windows大约有50个音量级别
            for _ in range(steps):
                pyautogui.press("volumeup")
        elif sys.platform == "linux":  # Linux
            # 先将音量调至最低
            for _ in range(50):  # 确保音量降至最低
                pyautogui.press("volumedown")

            # 然后根据请求的音量级别调整
            steps = int(volume_req.level / 100 * 50)  # Linux大约有50个音量级别
            for _ in range(steps):
                pyautogui.press("volumeup")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
            )

        logger.info(f"System volume set to {volume_req.level} successfully")
        return {"status": "success", "message": f"Volume set to {volume_req.level}"}
    except Exception as e:
        logger.error(f"Error setting system volume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}"
        )


@mediaRouter.post("/play")
async def play_media(user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    try:
        # 使用pyautogui执行媒体播放命令
        if sys.platform == "darwin":  # macOS
            pyautogui.keyDown("fn")
            pyautogui.keyDown("f7")
            pyautogui.keyUp("f7")
            pyautogui.keyUp("fn")  # macOS 播放/暂停键
        elif sys.platform == "win32":  # Windows
            pyautogui.press("playpause")  # Windows 播放/暂停键
        elif sys.platform == "linux":  # Linux
            pyautogui.press("playpause")  # Linux 播放/暂停键
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
            )

        logger.info("Media playback started successfully")
        return {"status": "success", "message": "Media playback started"}
    except Exception as e:
        logger.error(f"Error starting media playback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}"
        )


@mediaRouter.post("/pause")
async def pause_media(user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    try:
        # 使用pyautogui执行媒体暂停命令
        if sys.platform == "darwin":  # macOS
            pyautogui.keyDown("fn")
            pyautogui.keyDown("f7")
            pyautogui.keyUp("f7")
            pyautogui.keyUp("fn")  # macOS 播放/暂停键
        elif sys.platform == "win32":  # Windows
            pyautogui.press("playpause")  # Windows 播放/暂停键
        elif sys.platform == "linux":  # Linux
            pyautogui.press("playpause")  # Linux 播放/暂停键
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
            )

        logger.info("Media playback paused successfully")
        return {"status": "success", "message": "Media playback paused"}
    except Exception as e:
        logger.error(f"Error pausing media playback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}"
        )


@mediaRouter.post("/next")
async def next_track(user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    try:
        # 使用pyautogui执行下一首曲目命令
        if sys.platform == "darwin":  # macOS
            pyautogui.keyDown("fn")
            pyautogui.keyDown("f6")
            pyautogui.keyUp("f6")
            pyautogui.keyUp("fn")  # macOS 下一曲键
        elif sys.platform == "win32":  # Windows
            pyautogui.press("nexttrack")  # Windows 下一曲键
        elif sys.platform == "linux":  # Linux
            pyautogui.press("nexttrack")  # Linux 下一曲键
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
            )

        logger.info("Skipped to next track successfully")
        return {"status": "success", "message": "Skipped to next track"}
    except Exception as e:
        logger.error(f"Error skipping to next track: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}"
        )


@mediaRouter.post("/previous")
async def previous_track(user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    try:
        # 使用pyautogui执行上一首曲目命令
        if sys.platform == "darwin":  # macOS
            pyautogui.keyDown("fn")
            pyautogui.keyDown("f5")
            pyautogui.keyUp("f5")
            pyautogui.keyUp("fn")  # macOS 上一曲键
        elif sys.platform == "win32":  # Windows
            pyautogui.press("prevtrack")  # Windows 上一曲键
        elif sys.platform == "linux":  # Linux
            pyautogui.press("prevtrack")  # Linux 上一曲键
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform"
            )

        logger.info("Returned to previous track successfully")
        return {"status": "success", "message": "Returned to previous track"}
    except Exception as e:
        logger.error(f"Error returning to previous track: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}"
        )
