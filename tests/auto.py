import time

import pyautogui

print("诊断脚本将在 1 秒后开始...")
print("请准备好，不要移动鼠标。")
time.sleep(1)

# --- 鼠标功能测试 ---
print("\n--- 正在测试鼠标移动 ---")
try:
    # 获取初始位置
    start_pos = pyautogui.position()
    print(f"鼠标初始位置: {start_pos}")

    # 移动到屏幕 (100, 100) 的位置
    pyautogui.moveTo(100, 100, duration=1.5)
    end_pos = pyautogui.position()
    print(f"鼠标移动后位置: {end_pos}")

    if end_pos == (100, 100):
        print("✅ 鼠标移动功能正常！(辅助功能权限可能已正确设置)")
    else:
        print("❌ 鼠标移动失败！请检查【辅助功能】权限。")

except Exception as e:
    print(f"❌ 鼠标测试出错: {e}")

# 测试键盘输入
pyautogui.hotkey("fn", "f10")

# # --- 键盘功能测试 ---
# print("\n--- 正在测试键盘输入 ---")
# print("请在 1 秒内，手动点击打开一个文本文档或任何可以输入文字的地方...")
# time.sleep(1)

# try:
#     # 测试输入英文
#     pyautogui.typewrite("Hello, PyAutoGUI keyboard test.", interval=0.1)

#     # 测试独立的按键
#     pyautogui.press('enter')
#     pyautogui.typewrite("This is a new line.", interval=0.1)

#     print("\n✅ 键盘输入指令已发送。")
#     print("请检查你的文本编辑器里是否出现了'Hello...'和'This is a new line.'这两行字。")
#     print("如果文字出现了，说明键盘功能正常！(输入监控权限已正确设置)")
#     print("如果文字没有出现，说明键盘功能被阻止！请重点检查【输入监控】权限。")

# except Exception as e:
#     print(f"❌ 键盘测试出错: {e}")