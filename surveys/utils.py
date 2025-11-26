# surveys/utils.py
import os
from PIL import Image

def is_high_quality_image(image_path, min_width=1920, min_height=1080):
    """Проверяет, достаточно ли высокое разрешение фото"""
    try:
        with Image.open(image_path) as img:
            return img.width >= min_width and img.height >= min_height
    except Exception:
        return False