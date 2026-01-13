import os

import svgwrite

from .config import PROFILE_DATA

# Color configuration for themes
THEMES = {
    "dark": {
        "bg": "#0d1117",
        "text": "#c9d1d9",
        "key": "#e6c35c",
        "header": "#8b949e",
        "dots": "#30363d",
        "accent": "#79c0ff",
        "plus": "#56d364",
        "minus": "#f85149",
        "ascii": "#8b949e",
        "filename": "assets/profile-dark.svg",
    },
    "light": {
        "bg": "#ffffff",
        "text": "#24292f",
        "key": "#d4a72c",
        "header": "#57606a",
        "dots": "#d0d7de",
        "accent": "#0969da",
        "plus": "#1a7f37",
        "minus": "#cf222e",
        "ascii": "#57606a",
        "filename": "assets/profile-light.svg",
    },
}


def generate_svg(theme_name, stats_data, ascii_frames):
    """
    Generates an SVG file for the given theme, statistics, and ASCII animation frames.

    The layout consists of:
    - Left side: Animated ASCII art (slideshow)
    - Right side: System info style statistics (Neofetch style)
    """
    theme = THEMES[theme_name]
    total_width = 985
    height = 530

    right_column_start = 400

    dwg = svgwrite.Drawing(
        theme["filename"], profile="full", size=(total_width, height)
    )

    # --- CSS ANIMATION FOR SLIDESHOW ---
    num_frames = len(ascii_frames)
    duration_per_frame = 5  # seconds
    total_duration = num_frames * duration_per_frame
    slideshow_css = ""

    if num_frames > 1:
        for i in range(num_frames):
            anim_name = f"slide-anim-{i}"
            start_pct = (i / num_frames) * 100
            end_pct = ((i + 1) / num_frames) * 100

            keyframes = f"@keyframes {anim_name} {{"
            if i > 0:
                keyframes += "0% { opacity: 0; }"
            keyframes += f"{start_pct - 0.1:.1f}% {{ opacity: 0; }}"
            keyframes += f"{start_pct:.1f}% {{ opacity: 1; }}"
            keyframes += f"{end_pct - 0.1:.1f}% {{ opacity: 1; }}"
            keyframes += f"{end_pct:.1f}% {{ opacity: 0; }}"
            if i < num_frames - 1:
                keyframes += "100% { opacity: 0; }"
            keyframes += "}"

            slideshow_css += keyframes + "\n"
            slideshow_css += (
                f".slide-{i} {{ animation: {anim_name} {total_duration}s infinite; }}\n"
            )

    # --- CSS STYLES ---
    dwg.defs.add(
        dwg.style(f"""
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');
        text {{ font-family: 'Fira Code', monospace; font-size: 13px; fill: {theme["text"]}; }}
        .key {{ font-weight: bold; fill: {theme["key"]}; }}
        .header {{ fill: {theme["header"]}; }}
        .dots {{ fill: {theme["dots"]}; }}
        .plus {{ fill: {theme["plus"]}; font-weight: bold; }}
        .minus {{ fill: {theme["minus"]}; font-weight: bold; }}
        .ascii {{ fill: {theme["ascii"]}; font-size: 11px; white-space: pre; letter-spacing: 1px; }}
        {slideshow_css}
    """)
    )

    dwg.add(
        dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, fill=theme["bg"])
    )

    # --- CALCULATE HEIGHT OF RIGHT COLUMN ---
    content_y = 20
    row_height = 20

    right_column_height = 0
    for item in PROFILE_DATA:
        if item["type"] == "spacer":
            right_column_height += item.get("height", 10)
        elif item["type"] == "header":
            right_column_height += row_height
        elif item["type"] == "text":
            char_width = 7
            max_chars = int((total_width - right_column_start - 20) / char_width)
            text_lines = len(item["text"]) // max_chars + 1
            right_column_height += text_lines * row_height
        elif item["type"] == "group":
            right_column_height += len(item["items"]) * row_height
        elif item["type"] == "complex_loc":
            right_column_height += row_height
        elif item["type"] == "two_column":
            right_column_height += len(item["rows"]) * row_height

    final_height = max(right_column_height + content_y + 30, height)

    # --- LEFT SIDE (ASCII SLIDESHOW) ---
    max_frame_lines = max(len(frame) for frame in ascii_frames) if ascii_frames else 0
    line_height = 12
    max_ascii_height = max_frame_lines * line_height
    group_y_offset = max(20, (final_height - max_ascii_height) // 2)

    slideshow_group = dwg.g(transform=f"translate(20, {group_y_offset})")

    for i, frame in enumerate(ascii_frames):
        frame_class = f"slide-{i}" if num_frames > 1 else ""
        frame_style = "opacity: 1;" if i == 0 else "opacity: 0;"
        if num_frames == 1:
            frame_style = ""

        frame_height = len(frame) * line_height
        frame_y_offset = (max_ascii_height - frame_height) // 2

        frame_group = dwg.g(
            class_=frame_class,
            style=frame_style,
            transform=f"translate(0, {frame_y_offset})",
        )

        for line_idx, line in enumerate(frame):
            frame_group.add(dwg.text(line, insert=(0, line_idx * 12), class_="ascii"))

        slideshow_group.add(frame_group)

    dwg.add(slideshow_group)

    # --- RIGHT SIDE (TEXT RENDERER) ---
    content_x = right_column_start
    max_text_width = total_width - right_column_start - 20

    stats_group = dwg.g(transform=f"translate({content_x}, {content_y})")
    current_y = 0

    for item in PROFILE_DATA:
        if item["type"] == "spacer":
            current_y += item.get("height", 10)
            continue

        if item["type"] == "header":
            base_text = item["text"].rstrip("-").rstrip()
            char_width = 7
            available_chars = int(max_text_width / char_width)
            dashes_needed = available_chars - len(base_text) - 1
            header_text = base_text + " " + ("-" * max(0, dashes_needed))
            stats_group.add(
                dwg.text(header_text, insert=(0, current_y), class_="header")
            )
            current_y += row_height
            continue

        if item["type"] == "text":
            char_width = 7
            dot_prefix = ". "
            dot_prefix_width = len(dot_prefix) * char_width
            max_chars = int((max_text_width - dot_prefix_width) / char_width)
            text = item["text"]

            if len(text) > max_chars:
                lines = wrap_text(text, max_chars)
            else:
                lines = [text]

            for i, line in enumerate(lines):
                if i == 0:
                    stats_group.add(
                        dwg.text(dot_prefix, insert=(0, current_y), class_="dots")
                    )
                stats_group.add(
                    dwg.text(
                        line, insert=(dot_prefix_width, current_y), class_="header"
                    )
                )
                current_y += row_height
            continue

        if item["type"] == "group":
            char_width = 7
            dot_prefix = ". "
            dot_prefix_width = len(dot_prefix) * char_width

            for key, raw_val in item["items"]:
                val_text = raw_val.format(**stats_data)
                stats_group.add(
                    dwg.text(dot_prefix, insert=(0, current_y), class_="dots")
                )
                lines_used = draw_neofetch_row(
                    dwg,
                    stats_group,
                    key,
                    val_text,
                    dot_prefix_width,
                    current_y,
                    max_text_width - dot_prefix_width,
                    row_height,
                )
                current_y += row_height * lines_used
            continue

        if item["type"] == "two_column":
            char_width = 7
            half_width = max_text_width // 2 - 10
            dot_prefix = ". "
            dot_prefix_width = len(dot_prefix) * char_width

            for row in item["rows"]:
                left_key, left_val = row[0]
                right_key, right_val = row[1]

                left_val_text = left_val.format(**stats_data)
                right_val_text = right_val.format(**stats_data)

                stats_group.add(
                    dwg.text(dot_prefix, insert=(0, current_y), class_="dots")
                )

                draw_two_col_item(
                    dwg,
                    stats_group,
                    left_key,
                    left_val_text,
                    dot_prefix_width,
                    current_y,
                    half_width - dot_prefix_width,
                    char_width,
                )

                stats_group.add(
                    dwg.text("|", insert=(half_width + 5, current_y), class_="dots")
                )

                draw_two_col_item(
                    dwg,
                    stats_group,
                    right_key,
                    right_val_text,
                    half_width + 20,
                    current_y,
                    half_width,
                    char_width,
                )

                current_y += row_height
            continue

        if item["type"] == "complex_loc":
            key = item["label"]
            total = stats_data.get("loc_total", "0")
            add = stats_data.get("loc_add", "0")
            dele = stats_data.get("loc_del", "0")

            char_width = 7
            dot_prefix = ". "
            dot_prefix_width = len(dot_prefix) * char_width
            key_pixel_width = (len(key) + 1) * char_width

            value_text = f"{total} ( {add}, {dele} )"
            val_pixel_width = len(value_text) * char_width
            val_start_x = max_text_width - val_pixel_width

            stats_group.add(dwg.text(dot_prefix, insert=(0, current_y), class_="dots"))

            stats_group.add(
                dwg.text(f"{key}:", insert=(dot_prefix_width, current_y), class_="key")
            )

            space_for_dots = val_start_x - dot_prefix_width - key_pixel_width - 5
            if space_for_dots > 0:
                num_dots = int(space_for_dots / char_width)
                stats_group.add(
                    dwg.text(
                        "." * num_dots,
                        insert=(dot_prefix_width + key_pixel_width, current_y),
                        class_="dots",
                    )
                )

            val_group = dwg.text("", insert=(val_start_x, current_y))
            val_group.add(dwg.tspan(f"{total} "))
            val_group.add(dwg.tspan("( "))
            val_group.add(dwg.tspan(f"{add}", class_="plus"))
            val_group.add(dwg.tspan(", "))
            val_group.add(dwg.tspan(f"{dele}", class_="minus"))
            val_group.add(dwg.tspan(" )"))
            stats_group.add(val_group)

            current_y += row_height

    dwg.add(stats_group)

    actual_height = max(current_y + content_y + 30, final_height)
    dwg["height"] = f"{actual_height}px"

    os.makedirs(os.path.dirname(theme["filename"]), exist_ok=True)
    dwg.save()
    print(f"Generated: {theme['filename']}")


def draw_neofetch_row(dwg, group, key, value, x, y, max_width, row_height=20):
    """Draws a key-value row with dots in between (neofetch style).
    Returns the number of rows used (for text wrapping)."""
    char_width = 7
    key_pixel_width = (len(key) + 1) * char_width

    available_width = max_width - key_pixel_width - 20
    max_value_chars = int(available_width / char_width)

    if len(value) > max_value_chars and max_value_chars > 0:
        lines = wrap_text(value, max_value_chars)
    else:
        lines = [value]

    group.add(dwg.text(f"{key}:", insert=(x, y), class_="key"))

    first_line = lines[0]
    val_pixel_width = len(first_line) * char_width
    val_start_x = x + max_width - val_pixel_width
    if val_start_x < x + key_pixel_width + 10:
        val_start_x = x + key_pixel_width + 10

    group.add(dwg.text(first_line, insert=(val_start_x, y)))

    dot_start = x + key_pixel_width
    space_for_dots = val_start_x - dot_start - 5
    if space_for_dots > 0:
        num_dots = int(space_for_dots / char_width)
        group.add(dwg.text("." * num_dots, insert=(dot_start, y), class_="dots"))

    for i, line in enumerate(lines[1:], start=1):
        line_y = y + i * row_height
        group.add(dwg.text(line, insert=(val_start_x, line_y)))

    return len(lines)


def draw_two_col_item(dwg, group, key, value, x, y, width, char_width):
    key_pixel_width = (len(key) + 1) * char_width
    val_pixel_width = len(value) * char_width

    group.add(dwg.text(f"{key}:", insert=(x, y), class_="key"))

    val_start_x = x + width - val_pixel_width
    if val_start_x < x + key_pixel_width + 5:
        val_start_x = x + key_pixel_width + 5

    group.add(dwg.text(value, insert=(val_start_x, y)))

    space_for_dots = val_start_x - (x + key_pixel_width) - 3
    if space_for_dots > 0:
        num_dots = int(space_for_dots / char_width)
        group.add(
            dwg.text("." * num_dots, insert=(x + key_pixel_width, y), class_="dots")
        )


def wrap_text(text, max_chars):
    if len(text) <= max_chars:
        return [text]

    lines = []
    remaining = text

    while len(remaining) > max_chars:
        break_point = max_chars

        comma_pos = remaining[:max_chars].rfind(",")
        if comma_pos > max_chars // 2:
            break_point = comma_pos + 1
        else:
            space_pos = remaining[:max_chars].rfind(" ")
            if space_pos > max_chars // 3:
                break_point = space_pos + 1

        lines.append(remaining[:break_point].strip())
        remaining = remaining[break_point:].strip()

    if remaining:
        lines.append(remaining)

    return lines
