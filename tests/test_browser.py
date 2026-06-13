import importlib
import os

from PyQt5.QtCore import QUrl


def test_translations_have_same_keys():
    browser = importlib.import_module("Browser")
    expected_keys = set(browser.TRANSLATIONS[browser.DEFAULT_LANGUAGE])

    for translation in browser.TRANSLATIONS.values():
        assert set(translation) == expected_keys


def test_chromium_flags_are_configured_before_webengine_import():
    browser = importlib.import_module("Browser")

    assert os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] == (
        f"--host-resolver-rules=MAP * ~NOTFOUND,EXCLUDE {browser.I2P_PROXY_HOST}"
    )


def test_qurl_from_user_input_handles_common_address_forms():
    cases = {
        "example.com": "http://example.com",
        " https://example.com ": "https://example.com",
        "HTTPS://example.com": "https://example.com",
        "about:blank": "about:blank",
    }

    for raw_url, expected_url in cases.items():
        assert QUrl.fromUserInput(raw_url.strip()).toString() == expected_url
