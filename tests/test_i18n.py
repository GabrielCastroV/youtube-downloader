"""Tests for i18n.py."""

from __future__ import annotations

from yt_downloader.i18n import Translator


def test_default_language_is_es() -> None:
    t = Translator()
    assert t.language == "es"


def test_es_translation() -> None:
    t = Translator("es")
    assert t("ui.download") == "Descargar"
    assert t("app.title") == "YT Downloader"


def test_en_translation() -> None:
    t = Translator("en")
    assert t("ui.download") == "Download"
    assert t("error.invalid_url") != ""


def test_language_switch() -> None:
    t = Translator("es")
    assert "Descargar" in t("ui.download")
    t.set_language("en")
    assert "Download" in t("ui.download")


def test_callable_shortcut() -> None:
    t = Translator("en")
    assert t("ui.download") == t.get("ui.download")


def test_missing_key_returns_key() -> None:
    t = Translator("en")
    assert t("nonexistent.key") == "nonexistent.key"


def test_interpolation() -> None:
    t = Translator("en")
    result = t("ui.video_count", n="5")
    assert "5" in result


def test_all_keys_present_in_both_languages() -> None:
    t_es = Translator("es")
    t_en = Translator("en")
    # A sample of critical keys must be non-empty in both languages
    keys = [
        "ui.download",
        "ui.cancel",
        "error.invalid_url",
        "error.network",
        "ui.mode.video_audio",
        "ui.mode.audio",
        "ui.mode.video",
    ]
    for key in keys:
        assert t_es(key) != key, f"Missing ES key: {key}"
        assert t_en(key) != key, f"Missing EN key: {key}"
