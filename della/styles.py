from typing import Optional


def make_style(
    fg: Optional[str] = None, bg: Optional[str] = None, extra: Optional[str] = None
):
    fg_styling = f"fg:{fg}" if fg else None
    bg_styling = f"bg:{bg}" if bg else None

    return " ".join([s for s in (fg_styling, bg_styling, extra) if s])
