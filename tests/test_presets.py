"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Zahlen in den Hilfetexten stehen in test_claims.py."""

import rsp_constants as C
import rsp_evaluation as ev
import rsp_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(**first) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_the_enumeration_limit_matches_the_largest_slider_value():
    assert C.N_MAX == C.ENUM_MAX
    assert set(C.BAND_SIZES) == {C.ENUM_MAX, C.ENUM_MAX + 1}      # die vorberechneten Bänder decken die Live-Grenze und die nächste Größe ab


def test_every_preset_has_a_distinct_instance():
    keys = {(p["n"], p["family"], p["depot"], p["routes"], p["seed"]) for p in C.PRESETS.values()}
    assert len(keys) == len(C.PRESETS)
