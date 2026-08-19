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
    assert abs(_contrast_ratio("#ffffff", "#ffffff") - 1.0) < 0.01
    assert abs(_contrast_ratio("#767676", "#ffffff") - 4.54) < 0.01
    assert abs(_contrast_ratio("#595959", "#ffffff") - 7.0) < 0.01
    assert abs(_contrast_ratio("#ff0000", "#ffffff") - 3.998) < 0.01


def test_ink_passes_aa_on_every_light_surface():
    ink = PALETTE["ink"].hex
    for surface in ("app_background", "card", "sidebar_background", "sidebar_hover", "warm_neutral"):
        ratio = _contrast_ratio(ink, PALETTE[surface].hex)
        assert ratio >= 4.5, f"ink on {surface} is {ratio:.2f}:1"


def test_ink_muted_passes_aa_on_content_surfaces():
    ink_muted = PALETTE["ink_muted"].hex
    assert _contrast_ratio(ink_muted, PALETTE["app_background"].hex) >= 4.5
    assert _contrast_ratio(ink_muted, PALETTE["card"].hex) >= 4.5


def test_category_replicate_fails_on_white_and_is_prohibited():
    replicate = PALETTE["category_replicate"].hex
    assert _contrast_ratio(replicate, PALETTE["card"].hex) < 4.5
    assert "text_on_light" not in PALETTE["category_replicate"].permitted_uses


def test_accent_passes_aa_on_light_backgrounds():
    accent = PALETTE["accent"].hex
    assert _contrast_ratio(accent, PALETTE["card"].hex) >= 4.5
    assert _contrast_ratio(accent, PALETTE["app_background"].hex) >= 4.5
    assert _contrast_ratio(accent, PALETTE["sidebar_background"].hex) >= 4.5
    assert "text_on_light" in PALETTE["accent"].permitted_uses


def test_text_on_accent_passes_aa_against_accent_fill():
    # The selected navigation row and hovered sidebar buttons are accent fills
    # carrying this colour as their text.
    assert _contrast_ratio(PALETTE["text_on_accent"].hex, PALETTE["accent"].hex) >= 4.5


def test_decommission_colour_passes_aa_on_all_backgrounds():
    decommission = PALETTE["category_decommission"].hex
    assert decommission == "#9c4f1f"
    assert _contrast_ratio(decommission, PALETTE["app_background"].hex) >= 4.5
    assert _contrast_ratio(decommission, PALETTE["card"].hex) >= 4.5
    assert _contrast_ratio(decommission, PALETTE["warm_neutral"].hex) >= 4.5
    assert _contrast_ratio("#ffffff", decommission) >= 4.5


def test_warm_neutral_is_a_distinct_warm_tint_not_the_page_background():
    # Regression guard: warm_neutral was byte-identical to app_background after an
    # earlier restyle, which silently turned guard-rule badges into grey chrome.
    warm = PALETTE["warm_neutral"].hex
    assert warm != PALETTE["app_background"].hex
    assert warm != PALETTE["card"].hex
    r, g, b = (int(warm.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    assert r > b, "warm_neutral must be warm (more red than blue)"


def test_no_two_roles_share_a_hex_within_the_same_use_class():
    # Duplicate hexes are what made the warm_neutral (two fills, one value) and
    # header/heading (two text roles, one value) regressions invisible. White is
    # legitimately both a surface fill and text-on-dark, so the rule is scoped to
    # roles whose permitted uses actually overlap.
    roles = list(PALETTE.values())
    for i, first in enumerate(roles):
        for second in roles[i + 1:]:
            if first.hex != second.hex:
                continue
            overlap = set(first.permitted_uses) & set(second.permitted_uses)
            assert not overlap, (
                f"{first.role} and {second.role} share {first.hex} and overlap on {sorted(overlap)}"
            )


def test_every_text_on_light_role_actually_passes_aa():
    for role in PALETTE.values():
        if "text_on_light" in role.permitted_uses:
            ratio = _contrast_ratio(role.hex, PALETTE["app_background"].hex)
            assert ratio >= 4.5, f"{role.role} claims text_on_light but is {ratio:.2f}:1"


def test_fill_only_roles_do_not_claim_text_permissions():
    for name in ("app_background", "card", "sidebar_background", "sidebar_hover", "warm_neutral"):
        assert PALETTE[name].permitted_uses == ("fill",), f"{name} should be fill-only"


def test_retired_roles_are_gone():
    # header/heading/header_text were consolidated into ink and text_on_accent.
    for retired in ("header", "heading", "header_text"):
        assert retired not in PALETTE
