from bwace.app.theme import PALETTE


def _srgb_to_linear(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb_to_linear(r) + 0.7152 * _srgb_to_linear(g) + 0.0722 * _srgb_to_linear(b)


def _contrast_ratio(fg: str, bg: str) -> float:
    l1, l2 = _luminance(fg), _luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def test_checker_matches_known_wcag_anchors():
    assert abs(_contrast_ratio("#000000", "#ffffff") - 21.0) < 0.01
    assert abs(_contrast_ratio("#767676", "#ffffff") - 4.54) < 0.01
    assert abs(_contrast_ratio("#595959", "#ffffff") - 7.0) < 0.01


def test_dark_green_on_backgrounds_passes_aa():
    dark_green = PALETTE["header"].hex
    assert _contrast_ratio(dark_green, PALETTE["app_background"].hex) >= 4.5
    assert _contrast_ratio(dark_green, PALETTE["card"].hex) >= 4.5


def test_heading_colour_passes_aa():
    heading = PALETTE["heading"].hex
    assert _contrast_ratio(heading, PALETTE["app_background"].hex) >= 4.5
    assert _contrast_ratio(heading, PALETTE["card"].hex) >= 4.5


def test_accent_fails_on_white_and_is_prohibited():
    accent = PALETTE["accent"].hex
    assert _contrast_ratio(accent, PALETTE["card"].hex) < 4.5
    assert "text_on_light" not in accent  # sanity: hex string, not a role
    assert "text_on_light" not in PALETTE["accent"].permitted_uses


def test_decommission_colour_passes_aa_on_all_backgrounds():
    decommission = PALETTE["category_decommission"].hex
    assert decommission == "#9c4f1f"
    assert _contrast_ratio(decommission, PALETTE["app_background"].hex) >= 4.5
    assert _contrast_ratio(decommission, PALETTE["card"].hex) >= 4.5
    assert _contrast_ratio(decommission, PALETTE["warm_neutral"].hex) >= 4.5
    assert _contrast_ratio("#ffffff", decommission) >= 4.5


def test_no_role_used_for_text_on_light_lacks_permission():
    for role in PALETTE.values():
        if "text_on_light" in role.permitted_uses:
            ratio_on_app_bg = _contrast_ratio(role.hex, PALETTE["app_background"].hex)
            assert ratio_on_app_bg >= 4.5, f"{role.role} claims text_on_light but fails AA"
