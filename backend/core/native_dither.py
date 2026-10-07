"""Dithering for e-ink output: native C++ library with a pure-Python fallback.

The native library is optional. When it is missing or cannot be loaded (for
example on Windows, where the build script only produces an ELF shared object),
the pure-Python implementation below is used instead. Both paths share the same
Atkinson error-diffusion kernel and the same 4-colour palette, so the rendered
output is identical.
"""
from __future__ import annotations

import ctypes
import logging
import platform
from pathlib import Path

from PIL import Image

from .config import EINK_4COLOR_PALETTE

logger = logging.getLogger(__name__)

_EXT = ".dll" if platform.system() == "Windows" else ".so"
_LIB_PATH = Path(__file__).resolve().parent / "native" / f"libeink_dither{_EXT}"
_LIB: ctypes.CDLL | None = None
_BUILD_HINT = "run 'python3 backend/scripts/build_native_dither.py' from the repository root"

# Atkinson error-diffusion kernel: (dx, dy, weight), weights expressed in eighths.
_KERNEL = ((1, 0, 1), (2, 0, 1), (-1, 1, 1), (0, 1, 1), (1, 1, 1), (0, 2, 1))
_PALETTE_RGB = tuple(
    tuple(EINK_4COLOR_PALETTE[index * 3:index * 3 + 3]) for index in range(4)
)
_ALLOWED_3 = (0, 1, 3)
_ALLOWED_4 = (0, 1, 2, 3)


def _load_lib() -> ctypes.CDLL:
    global _LIB
    if _LIB is not None:
        return _LIB
    if not _LIB_PATH.exists():
        raise RuntimeError(f"native dithering library not found at {_LIB_PATH}; {_BUILD_HINT}")
    try:
        lib = ctypes.CDLL(str(_LIB_PATH))
        lib.inksight_atkinson_bw.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        lib.inksight_atkinson_bw.restype = ctypes.c_int
        lib.inksight_atkinson_palette.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        lib.inksight_atkinson_palette.restype = ctypes.c_int
        _LIB = lib
        return lib
    except OSError as exc:
        raise RuntimeError(f"failed to load native dithering library at {_LIB_PATH}: {exc}") from exc


def _try_load_lib() -> ctypes.CDLL | None:
    """Return the native library, or None when the optional build is absent."""
    try:
        return _load_lib()
    except RuntimeError as exc:
        logger.debug("Native dithering unavailable, using pure Python: %s", exc)
        return None


def _python_atkinson_bw(gray: Image.Image) -> Image.Image:
    src = gray.convert("L")
    width, height = src.size
    data = [float(value) for value in src.tobytes()]
    out = bytearray(width * height)
    kernel = _KERNEL
    for y in range(height):
        row = y * width
        for x in range(width):
            pos = row + x
            old_value = data[pos]
            new_value = 255.0 if old_value >= 128.0 else 0.0
            out[pos] = 255 if new_value else 0
            error = old_value - new_value
            if error == 0.0:
                continue
            for dx, dy, weight in kernel:
                nx = x + dx
                ny = y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    npos = ny * width + nx
                    value = data[npos] + error * (weight / 8.0)
                    if value < 0.0:
                        value = 0.0
                    elif value > 255.0:
                        value = 255.0
                    data[npos] = value
    return Image.frombytes("L", (width, height), bytes(out)).convert("1", dither=Image.Dither.NONE)


def _python_atkinson_palette(rgb: Image.Image, colors: int) -> Image.Image:
    if colors not in (3, 4):
        raise ValueError("palette Atkinson dithering supports only 3 or 4 colors")
    src = rgb.convert("RGB")
    width, height = src.size
    data = [float(value) for value in src.tobytes()]
    out = bytearray(width * height)
    kernel = _KERNEL
    palette = _PALETTE_RGB
    allowed = _ALLOWED_3 if colors == 3 else _ALLOWED_4
    for y in range(height):
        row = y * width
        for x in range(width):
            pos = row + x
            base = pos * 3
            red = data[base]
            green = data[base + 1]
            blue = data[base + 2]
            best = allowed[0]
            best_dist = -1.0
            for index in allowed:
                pr, pg, pb = palette[index]
                dr = red - pr
                dg = green - pg
                db = blue - pb
                dist = dr * dr + dg * dg + db * db
                if best_dist < 0.0 or dist < best_dist:
                    best_dist = dist
                    best = index
            out[pos] = best
            pr, pg, pb = palette[best]
            err_r = red - pr
            err_g = green - pg
            err_b = blue - pb
            if err_r == 0.0 and err_g == 0.0 and err_b == 0.0:
                continue
            for dx, dy, weight in kernel:
                nx = x + dx
                ny = y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    nbase = (ny * width + nx) * 3
                    factor = weight / 8.0
                    value = data[nbase] + err_r * factor
                    data[nbase] = 0.0 if value < 0.0 else 255.0 if value > 255.0 else value
                    value = data[nbase + 1] + err_g * factor
                    data[nbase + 1] = 0.0 if value < 0.0 else 255.0 if value > 255.0 else value
                    value = data[nbase + 2] + err_b * factor
                    data[nbase + 2] = 0.0 if value < 0.0 else 255.0 if value > 255.0 else value
    result = Image.frombytes("P", (width, height), bytes(out))
    result.putpalette(EINK_4COLOR_PALETTE + [0] * (768 - len(EINK_4COLOR_PALETTE)))
    return result


def atkinson_bw(gray: Image.Image) -> Image.Image:
    lib = _try_load_lib()
    if lib is None:
        return _python_atkinson_bw(gray)
    src = gray.convert("L")
    w, h = src.size
    in_buf = src.tobytes()
    out_buf = ctypes.create_string_buffer(w * h)
    err_buf = ctypes.create_string_buffer(256)
    status = lib.inksight_atkinson_bw(
        in_buf,
        w,
        h,
        out_buf,
        err_buf,
        len(err_buf),
    )
    if status != 0:
        raise RuntimeError(f"native black/white Atkinson dithering failed: {err_buf.value.decode('utf-8', errors='replace')}")
    return Image.frombytes("L", (w, h), out_buf.raw).convert("1", dither=Image.Dither.NONE)


def atkinson_palette(rgb: Image.Image, colors: int) -> Image.Image:
    lib = _try_load_lib()
    if lib is None:
        return _python_atkinson_palette(rgb, colors)
    if colors not in (3, 4):
        raise ValueError("native palette Atkinson dithering supports only 3 or 4 colors")
    src = rgb.convert("RGB")
    w, h = src.size
    in_buf = src.tobytes()
    out_buf = ctypes.create_string_buffer(w * h)
    err_buf = ctypes.create_string_buffer(256)
    status = lib.inksight_atkinson_palette(
        in_buf,
        w,
        h,
        int(colors),
        out_buf,
        err_buf,
        len(err_buf),
    )
    if status != 0:
        raise RuntimeError(f"native palette Atkinson dithering failed: {err_buf.value.decode('utf-8', errors='replace')}")
    out = Image.frombytes("P", (w, h), out_buf.raw)
    out.putpalette(EINK_4COLOR_PALETTE + [0] * (768 - len(EINK_4COLOR_PALETTE)))
    return out
