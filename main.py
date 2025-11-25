from PIL import Image
import matplotlib.font_manager as fm
import keyboard
import pyperclip
from pathlib import Path
import time
import subprocess
import tempfile
import shutil
import sys
import io

import config
import picture_spawner

# 全局热键变量
CONFIG_FILE = "config.json"
AVATAR_FILE = "avatar.png"
BACKGROUND_FILE = "background.png"
USERNAME = "匿名"
WANT_AUTO_SEND = 0
global HOTKEY
HOTKEY = "enter"


# 预定义的字体列表（需要根据系统调整路径）
FONTS_LIST = [

]

def copy_image_to_clipboard(img: Image.Image) -> bool:
    """
    把 PIL Image 拷贝到系统剪贴板（尝试 wl-copy、xclip、xsel），
    返回是否成功（True/False）。
    """
    # 平台区分：Windows 使用 Win32 API，其他平台尝试 wl-copy/xclip/xsel
    if sys.platform.startswith('win'):
        # 尝试使用 pywin32 的 win32clipboard
        try:
            import win32clipboard
            import win32con

            # 将 PIL Image 转为 DIB（BMP 的除文件头外部分）
            with io.BytesIO() as output:
                # Pillow 保存 BMP 会包含 14 字节的文件头，需要去掉
                img.convert('RGB').save(output, 'BMP')
                data = output.getvalue()
            # BMP 文件头为 14 字节，DIB 从第 14 字节开始
            dib = data[14:]

            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_DIB, dib)
            finally:
                win32clipboard.CloseClipboard()
            return True
        except ModuleNotFoundError:
            print('pywin32 未安装，Windows 上请安装 pywin32 (pip install pywin32) 以启用图片复制到剪贴板')
            return False
        except Exception as e:
            print('复制到 Windows 剪贴板失败:', e)
            return False
    else:
        # 首先把图片写入临时 PNG
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tf:
                tmp_path = tf.name
                img.save(tmp_path, format='PNG')
                tf.flush()

            with open(tmp_path, 'rb') as f:
                img_bytes = f.read()

            # 优先尝试 Wayland 的 wl-copy
            if shutil.which('wl-copy'):
                res = subprocess.run(['wl-copy', '--type', 'image/png'], input=img_bytes)
                return res.returncode == 0

            # 尝试 xclip
            if shutil.which('xclip'):
                res = subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i'], input=img_bytes)
                return res.returncode == 0

            # 尝试 xsel（支持可能有限）
            if shutil.which('xsel'):
                res = subprocess.run(['xsel', '--clipboard', '--input', '--mime-type', 'image/png'], input=img_bytes)
                return res.returncode == 0

            print('未找到支持图片复制到剪贴板的命令（wl-copy/xclip/xsel）。请安装其中之一以启用此功能。')
            return False
        finally:
            try:
                if tmp_path:
                    Path(tmp_path).unlink()
            except Exception:
                pass


def on_hotkey_pressed():
    """
    热键触发的回调：选中当前输入框内容（发送 Ctrl+A/Ctrl+C）、读取剪贴板文本，
    生成对话图片，并把图片放入剪贴板。
    """
    try:
        # 备份当前剪贴板文本（以便用户需要时可恢复）
        try:
            previous_clip = pyperclip.paste()
        except Exception:
            previous_clip = None

        # 发送全选与复制（Linux 使用 ctrl）
        keyboard.send('ctrl+a')
        time.sleep(0.06)
        keyboard.send('ctrl+x')
        time.sleep(0.5)
        # keyboard.send('backspace')

        # 读取剪贴板文本作为对话内容
        dialog_text = ''
        try:
            dialog_text = subprocess.check_output(["wl-paste"], text=True).strip()
        except Exception:
            dialog_text = ''

        if not dialog_text:
            print('未检测到剪贴板文本，取消生成。')
            return

        print('检测到文本，正在生成图片...')
        
        img = picture_spawner.generate_dialog_image(
            avatar_path=AVATAR_FILE,
            background_path=BACKGROUND_FILE,
            username=USERNAME,
            dialog_text=dialog_text,
            font_index=0,
            img_size=(1200, 300),
            output_path=None
        )

        ok = copy_image_to_clipboard(img)
        if ok:
            print('已将生成的图片放入剪贴板。')
        else:
            # 仍然把图片保存到临时文件供用户手动使用
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(tmp.name, format='PNG')
            print(f'无法直接复制图片到剪贴板，已将图片保存为: {tmp.name}')
        
        keyboard.send('ctrl+v')
        if (WANT_AUTO_SEND != 0):
            keyboard.send('enter')

    except Exception as e:
        print('热键回调发生错误:', e)


def start_hotkey_listener():
    """
    启动监听线程/循环，注册热键并保持运行。
    """
    # 读取配置中的 HOTKEY（如果有）
    print(f'注册热键: {HOTKEY}（按下时会复制当前输入框内容并生成图片）')
    try:
        keyboard.add_hotkey(HOTKEY, on_hotkey_pressed)
    except Exception as e:
        print('无法注册热键，请检查权限或 hotkey 字符串是否有效:', e)
        return 0

    print('监听中，按 Ctrl+C 退出。')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n已停止监听。')
        return 1


if __name__ == '__main__':
    HOTKEY = config.get_config_value(key = "hotkey")
    AVATAR_FILE = config.get_config_value(key = "avatar_image_path")
    BACKGROUND_FILE = config.get_config_value(key = "background_image_path")
    USERNAME = config.get_config_value(key = "username")
    WANT_AUTO_SEND = config.get_config_value(key = "want_auto_send")
    print(HOTKEY)
    print(AVATAR_FILE)
    print(BACKGROUND_FILE)
    print(USERNAME)
    if start_hotkey_listener() == 0:
        sys.exit(0)
    elif start_hotkey_listener() == 1:
        sys.exit(1)


# 使用示例
#sudo -E /home/GUEST/Documents/Python/ADVTextSpawner/.venv/bin/python main.py
# if __name__ == "__main__":
    
    '''
    # 生成对话框图片
    try:
        img = generate_dialog_image(
            avatar_path="avatar.png",
            background_path="background.jpg",
            username="GUEST",
            dialog_text="TES1234567890\n这是一个测试对话框，用于展示生成的图片效果。",
            font_index=0,
            img_size=(800, 200),
            output_path="output.png"
        )
        # img.show()
    except Exception as e:
        print(f"错误: {e}")
    #print(fm.findSystemFonts())
    '''

