import os

from PIL import Image, ImageEnhance, ImageOps

# ASCII character sets for different levels of detail
ASCII_CHARS_DETAILED = (
    "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
)
ASCII_CHARS_SIMPLE = "@%#*+=-:. "
ASCII_CHARS_BLOCKS = "█▓▒░ "

# Supported image file extensions
SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif")


def image_to_ascii(
    image_path, new_width=40, charset="simple", contrast=1.5, brightness=1.0
):
    """
    Converts a single image to a list of ASCII strings.

    Args:
        image_path (str): Path to the image file.
        new_width (int): Target width of the ASCII art in characters.
        charset (str): Choice of "simple", "detailed", or "blocks".
        contrast (float): Contrast multiplier (1.0 = original).
        brightness (float): Brightness multiplier (1.0 = original).
    """
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Failed to open image {image_path}: {e}")
        return ["ERROR", "IMAGE", "FAIL"]

    if charset == "detailed":
        chars = ASCII_CHARS_DETAILED
    elif charset == "blocks":
        chars = ASCII_CHARS_BLOCKS
    else:
        chars = ASCII_CHARS_SIMPLE

    # 1. Scaling (maintaining aspect ratio)
    width, height = img.size
    aspect_ratio = height / width
    # Monospaced fonts are roughly 2:1 height-to-width ratio, hence the 0.55 correction
    new_height = int(aspect_ratio * new_width * 0.55)
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 2. Convert to grayscale
    img = img.convert("L")

    # 3. Enhance contrast and brightness
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)

    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)

    # 4. Normalize histogram to use full 0-255 range
    img = ImageOps.autocontrast(img, cutoff=2)

    # 5. Map pixels to ASCII characters
    pixels = list(img.getdata())
    num_chars = len(chars)

    new_pixels = []
    for pixel in pixels:
        # Map pixel intensity (0-255) to character list index
        char_index = int((pixel / 255) * (num_chars - 1))
        new_pixels.append(chars[char_index])

    ascii_image = [
        "".join(new_pixels[index : index + new_width])
        for index in range(0, len(new_pixels), new_width)
    ]

    return ascii_image


def generate_ascii_slideshow(
    resources_dir, new_width=40, charset="simple", contrast=1.5, brightness=1.0
):
    """
    Scans the resources directory and converts all images to ASCII frames.

    Returns:
        list: A list where each element is a list of ASCII strings (one frame).
    """
    frames = []
    if not os.path.isdir(resources_dir):
        print(f"Directory {resources_dir} does not exist. Creating placeholder.")
        return [["DIR", "NOT", "FOUND"]]

    # Sort files by name for consistent animation sequence
    for filename in sorted(os.listdir(resources_dir)):
        if filename.lower().endswith(SUPPORTED_EXTENSIONS):
            filepath = os.path.join(resources_dir, filename)
            print(f"Processing image to ASCII: {filename}...")
            ascii_art = image_to_ascii(
                filepath, new_width, charset, contrast, brightness
            )
            frames.append(ascii_art)

    if not frames:
        print("No images found in resources directory. Creating placeholder.")
        return [["NO IMAGES", "FOUND", "IN RESOURCES"]]

    return frames
