import sys
import subprocess
import shutil
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from localctrl.logger import logger
from localctrl.user import Role, User, get_user

mediaRouter = APIRouter()


def _check_linux_command(command):
    """检查 Linux 系统上是否存在指定命令"""
    return shutil.which(command) is not None


def _get_linux_media_command():
    """获取 Linux 系统上可用的媒体控制命令"""
    if _check_linux_command("playerctl"):
        return "playerctl"
    elif _check_linux_command("xdotool"):
        return "xdotool"
    elif _check_linux_command("dbus-send"):
        return "dbus-send"
    else:
        return None


@mediaRouter.post("/mute")
async def mute(user: User = Depends(get_user)):
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    try:
        if sys.platform == "darwin":  # macOS
            # fn+f9 静音键
            subprocess.run(
                ["osascript", "-e", "set volume output muted true"], check=True
            )
        elif sys.platform == "win32":  # Windows
            subprocess.run(
                [
                    "powershell",
                    "-c",
                    "(New-Object -ComObject WScript.Shell).SendKeys([char]173)",
                ],
                check=True,
            )
        elif sys.platform == "linux":  # Linux
            if _check_linux_command("amixer"):
                subprocess.run(["amixer", "-q", "set", "Master", "mute"], check=True)
            elif _check_linux_command("pactl"):
                subprocess.run(
                    ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], check=True
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No suitable audio control command found on this Linux system",
                )
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
        if sys.platform == "darwin":  # macOS
            # fn+f9 静音键
            subprocess.run(
                ["osascript", "-e", "set volume output muted false"], check=True
            )
        elif sys.platform == "win32":  # Windows
            subprocess.run(
                [
                    "powershell",
                    "-c",
                    "(New-Object -ComObject WScript.Shell).SendKeys([char]173)",
                ],
                check=True,
            )
        elif sys.platform == "linux":  # Linux
            if _check_linux_command("amixer"):
                subprocess.run(["amixer", "-q", "set", "Master", "unmute"], check=True)
            elif _check_linux_command("pactl"):
                subprocess.run(
                    ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=True
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No suitable audio control command found on this Linux system",
                )
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
        if sys.platform == "darwin":  # macOS
            # macOS音量范围是0-10
            mac_volume = volume_req.level / 10
            subprocess.run(
                ["osascript", "-e", f"set volume output volume {mac_volume}"],
                check=True,
            )
        elif sys.platform == "win32":  # Windows
            # Windows使用nircmd设置音量 (需要安装nircmd)
            # nircmd的音量范围是0-65535
            win_volume = int(volume_req.level * 655.35)
            subprocess.run(["nircmd.exe", "setsysvolume", str(win_volume)], check=True)
        elif sys.platform == "linux":  # Linux
            if _check_linux_command("amixer"):
                subprocess.run(
                    ["amixer", "-q", "set", "Master", f"{volume_req.level}%"],
                    check=True,
                )
            elif _check_linux_command("pactl"):
                # pactl 音量范围是 0-65535
                pactl_volume = int(volume_req.level * 655.35)
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pactl_volume}"],
                    check=True,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No suitable audio control command found on this Linux system",
                )
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
        if sys.platform == "darwin":  # macOS
            # fn+f7 播放/暂停键
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 100'],
                check=True,
            )
        elif sys.platform == "win32":  # Windows
            subprocess.run(
                [
                    "powershell",
                    "-c",
                    "(New-Object -ComObject WScript.Shell).SendKeys([char]179)",
                ],
                check=True,
            )
        elif sys.platform == "linux":  # Linux
            linux_cmd = _get_linux_media_command()
            if linux_cmd == "playerctl":
                subprocess.run(["playerctl", "play"], check=True)
            elif linux_cmd == "xdotool":
                subprocess.run(["xdotool", "key", "XF86AudioPlay"], check=True)
            elif linux_cmd == "dbus-send":
                subprocess.run(
                    [
                        "dbus-send",
                        "--print-reply",
                        "--dest=org.mpris.MediaPlayer2.spotify",
                        "/org/mpris/MediaPlayer2",
                        "org.mpris.MediaPlayer2.Player.PlayPause",
                    ],
                    check=True,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No suitable media control command found on this Linux system",
                )
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
        if sys.platform == "darwin":  # macOS
            # fn+f7 播放/暂停键
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 100'],
                check=True,
            )
        elif sys.platform == "win32":  # Windows
            subprocess.run(
                [
                    "powershell",
                    "-c",
                    "(New-Object -ComObject WScript.Shell).SendKeys([char]179)",
                ],
                check=True,
            )
        elif sys.platform == "linux":  # Linux
            linux_cmd = _get_linux_media_command()
            if linux_cmd == "playerctl":
                subprocess.run(["playerctl", "pause"], check=True)
            elif linux_cmd == "xdotool":
                subprocess.run(["xdotool", "key", "XF86AudioPlay"], check=True)
            elif linux_cmd == "dbus-send":
                subprocess.run(
                    [
                        "dbus-send",
                        "--print-reply",
                        "--dest=org.mpris.MediaPlayer2.spotify",
                        "/org/mpris/MediaPlayer2",
                        "org.mpris.MediaPlayer2.Player.PlayPause",
                    ],
                    check=True,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No suitable media control command found on this Linux system",
                )
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
        if sys.platform == "darwin":  # macOS
            # fn+f6 下一曲键
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 99'],
                check=True,
            )
        elif sys.platform == "win32":  # Windows
            subprocess.run(
                [
                    "powershell",
                    "-c",
                    "(New-Object -ComObject WScript.Shell).SendKeys([char]176)",
                ],
                check=True,
            )
        elif sys.platform == "linux":  # Linux
            linux_cmd = _get_linux_media_command()
            if linux_cmd == "playerctl":
                subprocess.run(["playerctl", "next"], check=True)
            elif linux_cmd == "xdotool":
                subprocess.run(["xdotool", "key", "XF86AudioNext"], check=True)
            elif linux_cmd == "dbus-send":
                subprocess.run(
                    [
                        "dbus-send",
                        "--print-reply",
                        "--dest=org.mpris.MediaPlayer2.spotify",
                        "/org/mpris/MediaPlayer2",
                        "org.mpris.MediaPlayer2.Player.Next",
                    ],
                    check=True,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No suitable media control command found on this Linux system",
                )
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
        if sys.platform == "darwin":  # macOS
            # fn+f5 上一曲键
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 98'],
                check=True,
            )
        elif sys.platform == "win32":  # Windows
            subprocess.run(
                [
                    "powershell",
                    "-c",
                    "(New-Object -ComObject WScript.Shell).SendKeys([char]177)",
                ],
                check=True,
            )
        elif sys.platform == "linux":  # Linux
            linux_cmd = _get_linux_media_command()
            if linux_cmd == "playerctl":
                subprocess.run(["playerctl", "previous"], check=True)
            elif linux_cmd == "xdotool":
                subprocess.run(["xdotool", "key", "XF86AudioPrev"], check=True)
            elif linux_cmd == "dbus-send":
                subprocess.run(
                    [
                        "dbus-send",
                        "--print-reply",
                        "--dest=org.mpris.MediaPlayer2.spotify",
                        "/org/mpris/MediaPlayer2",
                        "org.mpris.MediaPlayer2.Player.Previous",
                    ],
                    check=True,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No suitable media control command found on this Linux system",
                )
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
