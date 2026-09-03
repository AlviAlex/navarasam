"""Utility to load and validate emojis against the ios_emoji.ttf font pack."""

import os
import struct
from functools import lru_cache
from typing import Set

# Variation selectors, zero-width joiners, and keycap combining modifiers
ALLOWED_MODIFIERS = {
    0xFE0E, 0xFE0F, 0x200D, 0x200B, 0x20E3,
    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
    0x23, 0x2A,
}


def _parse_ttf_cmap_codepoints(ttf_path: str) -> Set[int]:
    """Parse format 4 and format 12 cmap tables from a TTF font file to extract supported Unicode codepoints."""
    if not os.path.exists(ttf_path):
        return set()

    supported_cps: Set[int] = set()
    with open(ttf_path, "rb") as f:
        header = f.read(12)
        if len(header) < 12:
            return supported_cps

        _, num_tables = struct.unpack(">4sH", header[:6])
        tables = {}
        for _ in range(num_tables):
            tag_data = f.read(16)
            if len(tag_data) < 16:
                break
            tag, checksum, offset, length = struct.unpack(">4sIII", tag_data)
            tables[tag.decode("latin1", "ignore")] = (offset, length)

        if "cmap" not in tables:
            return supported_cps

        cmap_offset, _ = tables["cmap"]
        f.seek(cmap_offset)
        cmap_header = f.read(4)
        if len(cmap_header) < 4:
            return supported_cps

        version, num_subtables = struct.unpack(">HH", cmap_header)
        subtable_records = []
        for _ in range(num_subtables):
            rec = f.read(8)
            if len(rec) < 8:
                break
            platform_id, encoding_id, sub_offset = struct.unpack(">HHI", rec)
            subtable_records.append((platform_id, encoding_id, cmap_offset + sub_offset))

        for _, _, sub_offset in subtable_records:
            f.seek(sub_offset)
            sub_header = f.read(6)
            if len(sub_header) < 6:
                continue
            fmt = struct.unpack(">H", sub_header[:2])[0]

            if fmt == 12:
                # Format 12: Segmented coverage for 32-bit characters
                f.seek(sub_offset + 12)
                group_data = f.read(4)
                if len(group_data) < 4:
                    continue
                num_groups = struct.unpack(">I", group_data)[0]
                for _ in range(num_groups):
                    gdata = f.read(12)
                    if len(gdata) < 12:
                        break
                    start_char, end_char, _ = struct.unpack(">III", gdata)
                    for cp in range(start_char, end_char + 1):
                        supported_cps.add(cp)

            elif fmt == 4:
                # Format 4: Segment mapping to delta values (BMP)
                f.seek(sub_offset + 6)
                seg_data = f.read(8)
                if len(seg_data) < 8:
                    continue
                seg_count_x2 = struct.unpack(">H", seg_data[:2])[0]
                seg_count = seg_count_x2 // 2
                end_codes = [struct.unpack(">H", f.read(2))[0] for _ in range(seg_count)]
                f.read(2)  # reservedPad
                start_codes = [struct.unpack(">H", f.read(2))[0] for _ in range(seg_count)]
                for s, e in zip(start_codes, end_codes):
                    if s <= e and e != 0xFFFF:
                        for cp in range(s, e + 1):
                            supported_cps.add(cp)

    return supported_cps


@lru_cache(maxsize=1)
def get_supported_codepoints(font_path: str = "ios_emoji.ttf") -> Set[int]:
    """Get all supported Unicode codepoints from the emoji font pack."""
    # Check default path, relative to workspace or static folder
    candidates = [
        font_path,
        os.path.join(os.path.dirname(__file__), font_path),
        os.path.join(os.path.dirname(__file__), "static", "ios_emoji.ttf"),
    ]
    for path in candidates:
        if os.path.exists(path):
            cps = _parse_ttf_cmap_codepoints(path)
            if cps:
                return cps
    return set()


def is_emoji_supported(emoji_str: str, font_path: str = "ios_emoji.ttf") -> bool:
    """Check whether all primary codepoints in the emoji character or sequence are supported in the font pack."""
    supported = get_supported_codepoints(font_path)
    if not supported:
        # If font not loaded for some reason, allow standard unicode
        return True

    for char in emoji_str:
        cp = ord(char)
        if cp in ALLOWED_MODIFIERS or char.isspace():
            continue
        if cp not in supported:
            return False
    return True


def filter_supported_emojis(emoji_str: str, font_path: str = "ios_emoji.ttf") -> str:
    """Filter an emoji string so that only characters supported by the font pack remain."""
    supported = get_supported_codepoints(font_path)
    if not supported:
        return emoji_str

    cleaned_tokens = []
    # Split by whitespace or check cluster by cluster
    for token in emoji_str.split():
        if all(ord(c) in supported or ord(c) in ALLOWED_MODIFIERS for c in token):
            cleaned_tokens.append(token)
    return " ".join(cleaned_tokens) if cleaned_tokens else emoji_str
