"""Icon rendering rules for the generated iOS AppIcon master."""

from __future__ import annotations

import pytest

pytest.importorskip("PIL.Image")

from PIL import Image  # noqa: E402 - guarded by importorskip

from tools.make_app_icons import BACKGROUND_RGB, plate_bounds, render_icon  # noqa: E402


def _logo_with_margin(
    plate: tuple[int, int] = (120, 100),
    margin: int = 20,
) -> Image.Image:
    """Opaque plate on a transparent margin, mimicking the source artwork."""
    width = plate[0] + margin * 2
    height = plate[1] + margin * 2
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    box = (margin, margin, margin + plate[0], margin + plate[1])
    image.paste((0, 212, 255, 255), box)
    return image


def test_plate_bounds_drops_transparent_margin() -> None:
    assert plate_bounds(_logo_with_margin()) == (20, 20, 140, 120)


def test_plate_bounds_rejects_fully_transparent_source() -> None:
    with pytest.raises(ValueError):
        plate_bounds(Image.new("RGBA", (8, 8), (0, 0, 0, 0)))


def test_render_icon_is_square_and_opaque() -> None:
    icon = render_icon(_logo_with_margin(), size=64)
    assert icon.size == (64, 64)
    assert icon.mode == "RGB"


def test_render_icon_pads_with_the_hud_background() -> None:
    """A wider-than-tall plate is centred; the padding stays the HUD colour."""
    icon = render_icon(_logo_with_margin(plate=(120, 60)), size=120)
    assert icon.getpixel((60, 1)) == BACKGROUND_RGB
    assert icon.getpixel((60, 60)) != BACKGROUND_RGB


def test_render_icon_rejects_non_positive_size() -> None:
    with pytest.raises(ValueError):
        render_icon(_logo_with_margin(), size=0)
