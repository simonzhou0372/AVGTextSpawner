from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

FONTS_LIST = [

]

def get_available_font(font_index: int = 0, font_size: int = 32) -> ImageFont.FreeTypeFont:
    """
    固定使用 Pillow 包自带的可缩放字体（优先尝试 DejaVuSans.ttf），
    如果不可用则回退到 ImageFont.load_default()（位图字体，无法缩放）。

    这里忽略用户传入的 font_index，始终锁定为内部字体，满足“不需要用户自定义字体”的需求。
    """
    try: 
        return ImageFont.truetype("fonts/NotoSansCJK-Bold.ttc", font_size)
    except Exception:
        # 回退到 Pillow 的默认位图字体（可能无法按像素精确缩放）
        print("未获取到字体！")
        return ImageFont.load_default()


def wrap_text(text: str, max_width: int, font: ImageFont.FreeTypeFont) -> list:
    """
    文本换行处理
    
    Args:
        text: 原始文本
        max_width: 最大宽度（像素）
        font: 字体对象
    
    Returns:
        换行后的文本列表
    """
    words = text
    lines = []
    current_line = ""
    
    for char in words:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]
        
        if line_width > max_width:
            if current_line:
                lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    
    if current_line:
        lines.append(current_line)
    print("    wrap text成功！")
    return lines


def generate_dialog_image(
    avatar_path: str,
    background_path: str = None,
    username: str = "角色名称",
    dialog_text: str = "说话内容",
    font_index: int = 0,
    img_size: tuple = (1200, 800),
    output_path: str = None
) -> Image.Image:
    """
    生成对话框布局图片
    
    Args:
        avatar_path: 头像文件路径
        background_path: 背景文件路径，如果为None或文件不存在则使用纯黑背景
        username: 用户名称
        dialog_text: 说话内容
        font_index: 字体索引
        img_size: 图片大小 (width, height)，默认 (1200, 800)
        output_path: 输出文件路径，如果提供则保存图片
    
    Returns:
        PIL Image 对象
    """
    width, height = img_size
    
    # 创建或加载背景
    if background_path and Path(background_path).exists():
        try:
            bg_image = Image.open(background_path).convert("RGB")
            bg_image = bg_image.resize((width, height), Image.Resampling.LANCZOS)
            image = bg_image
        except:
            print("    未检测到背景图片，使用纯黑背景")
            image = Image.new("RGB", (width, height), color=(0, 0, 0))
    else:
        # 纯黑背景
        image = Image.new("RGB", (width, height), color=(0, 0, 0))
    
    draw = ImageDraw.Draw(image)
    
    # ===== 自适应调整头像大小 =====
    # 根据图片高度自动计算头像大小，约占高度的65%
    avatar_size = int(height * 0.65)
    avatar_padding = 30
    
    avatar = None
    if Path(avatar_path).exists():
        try:
            avatar = Image.open(avatar_path).convert("RGBA")
            avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        except:
            avatar = None
    
    # 粘贴头像到左下角
    if avatar:
        avatar_pos = (avatar_padding, height - avatar_size - avatar_padding)
        image.paste(avatar, avatar_pos, avatar)
    
    # ===== 自适应调整字体大小 =====
    # 根据图片尺寸自动调整字体大小（以图片高度的百分比），并设置最小字号以防止过小
    username_font_size = max(24, int(height * 0.1))  # 约高度的5%
    content_font_size = max(18, int(height * 0.15))  # 约高度的3.5%
    
    username_font = get_available_font(font_index, username_font_size)
    content_font = get_available_font(font_index, content_font_size)
    
    # ===== 文本框布局 =====
    text_box_x = avatar_size + avatar_padding + 20  # 头像右侧
    text_box_y = int(height * 0.1)  # 顶部边距
    text_box_width = width - text_box_x - 40
    text_box_height = height - text_box_y - 40
    
    # 用户名
    username_bbox = username_font.getbbox(username)
    username_height = username_bbox[3] - username_bbox[1]
    
    draw.text(
        (text_box_x, text_box_y),
        username,
        fill=(255, 200, 100),  # 金黄色
        font=username_font
    )
    
    # 说话内容（带文本换行）
    lines = wrap_text(dialog_text, text_box_width, content_font)
    
    # 计算内容框高度
    line_height = content_font.getbbox("A")[3] - content_font.getbbox("A")[1]
    total_text_height = len(lines) * line_height + (len(lines) - 1) * 10
    
    # 绘制半透明背景框
    content_start_y = text_box_y + username_height + 25
    
    # 调整文本框高度以适应内容
    content_height = min(total_text_height + 30, text_box_height - username_height - 30)
    
    # 绘制半透明黑色背景框
    dialog_box_coords = [
        (text_box_x - 10, content_start_y - 10),
        (text_box_x + text_box_width + 10, content_start_y + content_height)
    ]
    
    # 创建半透明背景
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        dialog_box_coords,
        fill=(20, 20, 40, 180)  # 深蓝色半透明
    )
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)
    
    # 绘制文本内容
    current_y = content_start_y
    for i, line in enumerate(lines):
        draw.text(
            (text_box_x, current_y),
            line,
            fill=(255, 255, 255),  # 白色
            font=content_font
        )
        current_y += line_height + 10
    
    # 保存图片
    if output_path:
        image.save(output_path)
        print(f"图片已保存到: {output_path}")
    
    return image