import app


def test_detect_style_pair():
    tags = ["melkor", "melkor_bt_style", "extra"]
    is_style, next_index = app.detect_style(tags, 0)

    assert is_style is True
    assert next_index == 2


def test_is_physical_trait_matches_hair():
    assert app.is_physical_trait("long hair with highlights")
    assert not app.is_physical_trait("arm raised")


def test_parse_prompt_separates_categories_and_trace():
    prompt = (
        "1girl, solo, blush, bikini, masterpiece, best quality, tsinne, 3d, outdoors"
    )
    categorized, trace = app.parse_prompt(prompt)

    assert categorized["Qualidade"] == ["masterpiece", "best quality"]
    assert categorized["Background"] == ["((simple background))"]
    assert "1girl" in categorized["Personagem"]
    assert "bikini" in categorized["Roupas"]
    assert "tsinne" in categorized["Restante do Prompt"]

    unmatched = [
        item for item in trace if item["tag"] == "tsinne" and item["motivo"] == "Sem regra aplicada"
    ]
    assert unmatched, "tsinne deveria ser sinalizado como sem regra específica"


def test_custom_rule_moves_tag_to_personagem():
    original_rules = app.CUSTOM_RULES.copy()
    try:
        app.CUSTOM_RULES = {"cyberpunk": "Personagem"}
        categorized, _ = app.parse_prompt("cyberpunk")
        assert categorized["Personagem"] == ["cyberpunk"]
    finally:
        app.CUSTOM_RULES = original_rules


def test_clothing_tag_detected_outside_character_section():
    categorized, _ = app.parse_prompt("thighhighs, boots")
    assert "thighhighs" in categorized["Roupas"]
    assert "boots" in categorized["Roupas"]
