from study_app.catalog import CAPABILITIES, MODULES, get_module


def test_catalog_has_eight_ordered_modules_with_existing_sources():
    assert len(MODULES) == 8
    assert [module.order for module in MODULES] == list(range(1, 9))
    assert len({module.id for module in MODULES}) == 8
    assert all(module.source.exists() for module in MODULES)


def test_bb84_prompt_has_four_capability_criteria():
    module = get_module("bb84-bases")
    assert module is not None
    assert module.prompt.prompt_id == "bb84-eve-qber-01"
    assert set(module.prompt.rubric) == set(CAPABILITIES)


def test_unknown_module_returns_none():
    assert get_module("missing") is None
