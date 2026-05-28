import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import PySide6


def configure_qt_environment():
    qt_plugins = Path(PySide6.__file__).resolve().parent / "Qt" / "plugins"
    platform_plugins = qt_plugins / "platforms"

    if qt_plugins.exists():
        os.environ["QT_PLUGIN_PATH"] = str(qt_plugins)

    if platform_plugins.exists():
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platform_plugins)

    if sys.platform == "darwin":
        os.environ.setdefault("QT_QPA_PLATFORM", "cocoa")


configure_qt_environment()

from PySide6.QtCore import QByteArray, QUrl
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtNetwork import QNetworkProxy
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


APP_DIR = Path(__file__).resolve().parent
APP_ICON = APP_DIR / "i2p_icon.png"
I2P_HOME_URL = "http://legwork.i2p/"
CLEARNET_HOME_URL = "https://i2pengine.com/"
ROUTER_CONSOLE_URL = "http://127.0.0.1:7657/"
I2P_PROXY_HOST = "127.0.0.1"
I2P_PROXY_PORT = 4444
TOR_PROXY_HOST = "127.0.0.1"
TOR_PROXY_PORT = 9050
DEFAULT_LANGUAGE = "en"

TRANSLATIONS = {
    "en": {
        "language_name": "English",
        "window_title": "I2P Browser",
        "back": "Back",
        "forward": "Forward",
        "reload": "Reload",
        "home": "Home",
        "router_console": "I2P Router Console",
        "proxy": "Proxy",
        "proxy_i2p": "I2P",
        "proxy_tor": "Tor",
        "proxy_none": "Direct",
        "proxy_status_disabled": "Proxy Status: Disabled",
        "proxy_status_i2p": "Proxy Status: I2P {host}:{port}",
        "proxy_status_tor": "Proxy Status: Tor {host}:{port}",
        "language": "Language",
        "accept_language": "en-US,en;q=0.5",
    },
    "zh_CN": {
        "language_name": "简体中文",
        "window_title": "I2P 浏览器",
        "back": "后退",
        "forward": "前进",
        "reload": "刷新",
        "home": "主页",
        "router_console": "I2P 路由控制台",
        "proxy": "代理",
        "proxy_i2p": "I2P",
        "proxy_tor": "Tor",
        "proxy_none": "直连",
        "proxy_status_disabled": "代理状态：已关闭",
        "proxy_status_i2p": "代理状态：I2P {host}:{port}",
        "proxy_status_tor": "代理状态：Tor {host}:{port}",
        "language": "语言",
        "accept_language": "zh-CN,zh;q=0.9,en;q=0.5",
    },
    "zh_TW": {
        "language_name": "繁體中文",
        "window_title": "I2P 瀏覽器",
        "back": "上一頁",
        "forward": "下一頁",
        "reload": "重新整理",
        "home": "首頁",
        "router_console": "I2P 路由控制台",
        "proxy": "代理",
        "proxy_i2p": "I2P",
        "proxy_tor": "Tor",
        "proxy_none": "直連",
        "proxy_status_disabled": "代理狀態：已關閉",
        "proxy_status_i2p": "代理狀態：I2P {host}:{port}",
        "proxy_status_tor": "代理狀態：Tor {host}:{port}",
        "language": "語言",
        "accept_language": "zh-TW,zh;q=0.9,en;q=0.5",
    },
}


class NWUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, headers):
        super().__init__()
        self.headers = headers

    def set_headers(self, headers):
        self.headers = headers

    def interceptRequest(self, info):
        for header, value in self.headers:
            info.setHttpHeader(
                QByteArray(header.encode()),
                QByteArray(value.encode()),
            )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.language = DEFAULT_LANGUAGE
        self.nav_buttons = {}
        self.setWindowTitle(self.tr_text("window_title"))
        self.setMinimumSize(1100, 720)

        # Creates a QWebEngineView
        self.browser = QWebEngineView()

        # Creates an off-the-record custom profile.
        self.profile = QWebEngineProfile(self)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
        )
        self.profile.cookieStore().setCookieFilter(self._allow_first_party_cookies_only)

        # Sets the custom profile for the browser
        self.browser.setPage(QWebEnginePage(self.profile, self.browser))

        # Disables JavaScript by default
        settings = self.browser.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, True)

        # Disables local storage (caching)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, False)

        # Disables file access
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)

        # Sets custom User-Agent string
        user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"
        self.browser.page().profile().setHttpUserAgent(user_agent)

        self._build_ui()

        QShortcut(QKeySequence.Refresh, self, activated=self.browser.reload)
        QShortcut(QKeySequence("Alt+Left"), self, activated=self.browser.back)
        QShortcut(QKeySequence("Alt+Right"), self, activated=self.browser.forward)

        # Connects the URL change signal to update the URL bar
        self.browser.urlChanged.connect(self.update_url)

        # Sets up proxies. I2P is enabled by default.
        self.proxy_mode = "none"
        self.i2p_proxy = QNetworkProxy()
        self.i2p_proxy.setType(QNetworkProxy.ProxyType.HttpProxy)
        self.i2p_proxy.setHostName(I2P_PROXY_HOST)
        self.i2p_proxy.setPort(I2P_PROXY_PORT)

        self.tor_proxy = QNetworkProxy()
        self.tor_proxy.setType(QNetworkProxy.ProxyType.Socks5Proxy)
        self.tor_proxy.setHostName(TOR_PROXY_HOST)
        self.tor_proxy.setPort(TOR_PROXY_PORT)

        # Initialize the NWUrlRequestInterceptor with default headers
        self.request_interceptor = NWUrlRequestInterceptor(self.default_headers())
        self.browser.page().profile().setUrlRequestInterceptor(self.request_interceptor)

        # Enables I2P proxy initially and set the initial URL
        self.proxy_selector.setCurrentIndex(self.proxy_selector.findData("i2p"))
        self.browser.setUrl(QUrl(I2P_HOME_URL))

    def _build_ui(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("appShell")
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        nav_bar = QFrame(self)
        nav_bar.setObjectName("navBar")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(12, 10, 12, 10)
        nav_layout.setSpacing(8)

        self.nav_buttons["back"] = self._create_nav_button("back", "‹", self.browser.back)
        self.nav_buttons["forward"] = self._create_nav_button("forward", "›", self.browser.forward)
        self.nav_buttons["reload"] = self._create_nav_button("reload", "⟳", self.browser.reload)
        self.nav_buttons["home"] = self._create_nav_button("home", "⌂", self.navigate_home)
        self.nav_buttons["router_console"] = self._create_nav_button(
            "router_console",
            "I2P",
            self.custom_redirect,
            "brandButton",
        )

        for button in self.nav_buttons.values():
            nav_layout.addWidget(button)

        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("urlBar")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_layout.addWidget(self.url_bar, 1)

        self.proxy_label = QLabel(self.tr_text("proxy"), self)
        self.proxy_label.setObjectName("controlLabel")
        nav_layout.addWidget(self.proxy_label)

        self.proxy_selector = QComboBox(self)
        self.proxy_selector.setObjectName("controlSelect")
        self.populate_proxy_selector()
        self.proxy_selector.currentIndexChanged.connect(self.change_proxy_mode)
        nav_layout.addWidget(self.proxy_selector)

        self.language_label = QLabel(self.tr_text("language"), self)
        self.language_label.setObjectName("controlLabel")
        nav_layout.addWidget(self.language_label)

        self.language_selector = QComboBox(self)
        self.language_selector.setObjectName("controlSelect")
        for language_code, translation in TRANSLATIONS.items():
            self.language_selector.addItem(translation["language_name"], language_code)
        self.language_selector.currentIndexChanged.connect(self.change_language)
        nav_layout.addWidget(self.language_selector)

        status_bar = QFrame(self)
        status_bar.setObjectName("statusBar")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(14, 6, 14, 6)
        status_layout.setSpacing(8)

        self.status_label = QLabel(self.tr_text("proxy_status_disabled"), self)
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)

        root_layout.addWidget(nav_bar)
        root_layout.addWidget(self.browser, 1)
        root_layout.addWidget(status_bar)

        self.setCentralWidget(central_widget)
        self.apply_styles()
        self.apply_language()

    def _create_nav_button(self, key, symbol, callback, object_name="navButton"):
        button = QPushButton(symbol, self)
        button.setObjectName(object_name)
        button.setFixedHeight(34)
        button.setMinimumWidth(40)
        button.clicked.connect(callback)
        button.setToolTip(self.tr_text(key))
        return button

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget#appShell {
                background: #f4f6f8;
                color: #1f2933;
                font-size: 13px;
            }

            QFrame#navBar {
                background: #ffffff;
                border-bottom: 1px solid #d9e2ec;
            }

            QPushButton#navButton,
            QPushButton#brandButton {
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                background: #f8fafc;
                color: #102a43;
                font-weight: 700;
                padding: 0 10px;
            }

            QPushButton#navButton:hover,
            QPushButton#brandButton:hover {
                background: #e0f2fe;
                border-color: #38bdf8;
            }

            QPushButton#navButton:pressed,
            QPushButton#brandButton:pressed {
                background: #bae6fd;
            }

            QPushButton#brandButton {
                color: #0f766e;
                min-width: 46px;
            }

            QLineEdit#urlBar {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background: #ffffff;
                padding: 7px 12px;
                selection-background-color: #bae6fd;
                font-size: 14px;
            }

            QLineEdit#urlBar:focus {
                border-color: #0284c7;
            }

            QLabel#controlLabel {
                color: #52616b;
                font-weight: 700;
                padding-left: 6px;
            }

            QComboBox#controlSelect {
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                background: #ffffff;
                padding: 5px 26px 5px 10px;
                min-width: 104px;
            }

            QComboBox#controlSelect:focus {
                border-color: #0284c7;
            }

            QFrame#statusBar {
                background: #ffffff;
                border-top: 1px solid #d9e2ec;
            }

            QLabel#statusLabel {
                font-weight: 700;
            }
        """)

    @staticmethod
    def _allow_first_party_cookies_only(request):
        return not request.thirdParty

    def tr_text(self, key):
        return TRANSLATIONS[self.language][key]

    def populate_proxy_selector(self):
        selected_mode = self.proxy_selector.currentData()
        self.proxy_selector.blockSignals(True)
        self.proxy_selector.clear()
        self.proxy_selector.addItem(self.tr_text("proxy_i2p"), "i2p")
        self.proxy_selector.addItem(self.tr_text("proxy_tor"), "tor")
        self.proxy_selector.addItem(self.tr_text("proxy_none"), "none")

        index = self.proxy_selector.findData(selected_mode or "i2p")
        self.proxy_selector.setCurrentIndex(max(index, 0))
        self.proxy_selector.blockSignals(False)

    def default_headers(self):
        return [
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"),
            ("Accept-Language", self.tr_text("accept_language")),
            ("Accept-Encoding", "gzip, deflate, br"),
        ]

    def change_language(self, _index=None):
        language_code = self.language_selector.currentData()
        if language_code not in TRANSLATIONS:
            return

        self.language = language_code
        self.request_interceptor.set_headers(self.default_headers())
        self.apply_language()

    def apply_language(self):
        self.setWindowTitle(self.tr_text("window_title"))

        for button_key, button in self.nav_buttons.items():
            button.setToolTip(self.tr_text(button_key))

        self.proxy_label.setText(self.tr_text("proxy"))
        self.populate_proxy_selector()
        self.language_label.setText(self.tr_text("language"))
        self.update_proxy_status()

    def change_proxy_mode(self, _index=None):
        mode = self.proxy_selector.currentData()
        if mode in {"i2p", "tor", "none"}:
            self._set_proxy_mode(mode)

    def _set_proxy_mode(self, mode):
        self.proxy_mode = mode

        if mode == "i2p":
            QNetworkProxy.setApplicationProxy(self.i2p_proxy)
        elif mode == "tor":
            QNetworkProxy.setApplicationProxy(self.tor_proxy)
        else:
            QNetworkProxy.setApplicationProxy(QNetworkProxy())

        self._sync_proxy_selector()
        self.update_proxy_status()

    def _sync_proxy_selector(self):
        index = self.proxy_selector.findData(self.proxy_mode)
        if index < 0 or index == self.proxy_selector.currentIndex():
            return

        self.proxy_selector.blockSignals(True)
        self.proxy_selector.setCurrentIndex(index)
        self.proxy_selector.blockSignals(False)

    def navigate_home(self):
        if self.proxy_mode == "i2p":
            # If the checkbox is checked, use the Legwork I2P URL
            self.browser.setUrl(QUrl(I2P_HOME_URL))
        else:
            # If the checkbox is unchecked, use the clearnet URL
            self.browser.setUrl(QUrl(CLEARNET_HOME_URL))

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url  # Adds 'http://' prefix if missing
        self.browser.setUrl(QUrl(url))

    def update_url(self, q):
        url = q.toString()
        parsed_url = urlsplit(url)
        hostname = parsed_url.hostname

        if url.startswith("https://"):
            self.url_bar.setStyleSheet("color: green;")
        elif hostname in {"localhost", "127.0.0.1"}:
            self.url_bar.setStyleSheet("color: black;")
        elif hostname and hostname.endswith(".i2p"):
            self.url_bar.setStyleSheet("color: green;")
        else:
            self.url_bar.setStyleSheet("color: red")

        self.url_bar.setText(url)


    def update_proxy_status(self):
        if self.proxy_mode == "i2p":
            self.status_label.setText(
                self.tr_text("proxy_status_i2p").format(
                    host=I2P_PROXY_HOST,
                    port=I2P_PROXY_PORT,
                )
            )
            self.status_label.setStyleSheet("color: green;")
        elif self.proxy_mode == "tor":
            self.status_label.setText(
                self.tr_text("proxy_status_tor").format(
                    host=TOR_PROXY_HOST,
                    port=TOR_PROXY_PORT,
                )
            )
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(self.tr_text("proxy_status_disabled"))
            self.status_label.setStyleSheet("color: red;")

    def custom_redirect(self):
        # Redirects to http://127.0.0.1:7657/ (I2P Router Console)
        self.browser.setUrl(QUrl(ROUTER_CONSOLE_URL))

    def closeEvent(self, event):
        # Clears browsing data when the application is closed
        self.browser.page().history().clear()
        self.browser.page().profile().clearAllVisitedLinks()
        event.accept()


def main():
    os.environ.setdefault(
        "QTWEBENGINE_CHROMIUM_FLAGS",
        f"--host-resolver-rules='MAP * ~NOTFOUND, EXCLUDE {I2P_PROXY_HOST}'",
    )

    app = QApplication(sys.argv)
    QApplication.setApplicationName("I2P Browser")
    app.setWindowIcon(QIcon(str(APP_ICON)))

    window = MainWindow()
    window.showMaximized()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
