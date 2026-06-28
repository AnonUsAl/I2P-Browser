

import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import PyQt5


APP_DIR = Path(__file__).resolve().parent
APP_ICON = APP_DIR / "i2p_icon.png"
HOME_PAGE = (APP_DIR / "home.html").as_uri()
I2P_HOME_URL = "http://ransack.i2p/"
CLEARNET_HOME_URL = "https://duckduckgo.com"
ROUTER_CONSOLE_URL = "http://127.0.0.1:7657/"
I2P_PROXY_HOST = "127.0.0.1"
I2P_PROXY_PORT = 4444
TOR_PROXY_HOST = "127.0.0.1"
TOR_PROXY_PORT = 9050
DEFAULT_LANGUAGE = "en"

# for macOS, set the QT_QPA_PLATFORM_PLUGIN_PATH and QT_PLUGIN_PATH environment variables.
#macOS requires these environment variables to be set for PyQt5 to find the necessary Qt plugins. This is especially important when running the application outside of a standard Python environment, such as when packaged with PyInstaller or similar tools.
#fuck macOS
#It takes me a lot of time to figure out this problem, and I hope this code can help others who encounter the same issue.   
#fuck macOS again!!!!!!!!!
def configure_qt_environment():
    pyqt_plugins = Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
    platform_plugins = pyqt_plugins / "platforms"

    if platform_plugins.exists():
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platform_plugins))

    if pyqt_plugins.exists():
        os.environ.setdefault("QT_PLUGIN_PATH", str(pyqt_plugins))

    if sys.platform == "darwin":
        os.environ.setdefault("QT_QPA_PLATFORM", "cocoa")


def configure_chromium_flags():
    # Disable GPU and sandbox on macOS to prevent crashes
    flags = "--disable-gpu --no-sandbox --disable-features=NetworkPrediction"
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", flags)


configure_qt_environment()
configure_chromium_flags()

from PyQt5.QtCore import QByteArray, Qt, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtNetwork import QNetworkProxy
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWebEngineWidgets import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineView,

)
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QToolBar,
)


TRANSLATIONS = {
    "en": {
        "language_name": "English",
        "window_title": "I2P Browser",
        "router_console": "I2P Router Console",
        "use_i2p_proxy": "I2P",
        "use_tor_proxy": "Tor",
        "javascript": "JS",
        "proxy_status_disabled": "Proxy Status: Disabled",
        "proxy_status_i2p": "Proxy Status: I2P {host}:{port}",
        "proxy_status_tor": "Proxy Status: Tor {host}:{port}",
        "language": "Language",
        "accept_language": "en-US,en;q=0.5",
    },
    "zh_CN": {
        "language_name": "简体中文",
        "window_title": "I2P 浏览器",
        "router_console": "I2P 路由控制台",
        "use_i2p_proxy": "使用 I2P 代理",
        "use_tor_proxy": "使用 Tor 代理",
        "javascript": "脚本",
        "proxy_status_disabled": "代理状态：已关闭",
        "proxy_status_i2p": "代理状态：I2P {host}:{port}",
        "proxy_status_tor": "代理状态：Tor {host}:{port}",
        "language": "语言",
        "accept_language": "zh-CN,zh;q=0.9,en;q=0.5",
    },
    "zh_TW": {
        "language_name": "繁體中文",
        "window_title": "I2P 瀏覽器",
        "router_console": "I2P 路由控制台",
        "use_i2p_proxy": "使用 I2P 代理",
        "use_tor_proxy": "使用 Tor 代理",
        "javascript": "腳本",
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
                QByteArray(header.encode("utf-8")),
                QByteArray(value.encode("utf-8")),
            )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.language = DEFAULT_LANGUAGE
        self.setWindowTitle(self.tr_text("window_title"))

        # Creates a QWebEngineView
        self.browser = QWebEngineView()

        # Creates an off-the-record custom profile.
        self.profile = QWebEngineProfile(self)
        self.profile.setHttpCacheType(QWebEngineProfile.NoCache)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        cookie_store = self.profile.cookieStore()
        if hasattr(cookie_store, "setCookieFilter"):
            cookie_store.setCookieFilter(self._allow_first_party_cookies_only)

        # Sets the custom profile for the browser
        self.browser.setPage(QWebEnginePage(self.profile, self.browser))

        # Enables JavaScript by default (togglable via toolbar switch)
        settings = self.browser.page().settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebRTCPublicInterfacesOnly, True)  # Disable WebRTC

        # Disables local storage (caching)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, False)

        # Disables file access
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)

        # Sets custom User-Agent string
        user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"
        self.browser.page().profile().setHttpUserAgent(user_agent)

        # Sets the central widget
        self.setCentralWidget(self.browser)

        # Shows the window maximized
        self.showMaximized()

        # Creates a navigation toolbar
        navbar = QToolBar()
        self.addToolBar(navbar)

        # Adds navigation actions (Back, Forward, Reload, Home)
        back_btn = QAction("◀", self)
        back_btn.triggered.connect(self.browser.back)
        navbar.addAction(back_btn)

        forward_btn = QAction("▶", self)
        forward_btn.triggered.connect(self.browser.forward)
        navbar.addAction(forward_btn)

        reload_btn = QAction("↻", self)
        reload_btn.triggered.connect(self.browser.reload)
        navbar.addAction(reload_btn)

        home_btn = QAction("🏠", self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        # Button for I2P Router Console
        self.router_console_btn = QAction(QIcon(str(APP_ICON)), self.tr_text("router_console"), self)
        self.router_console_btn.triggered.connect(self.custom_redirect)
        navbar.addAction(self.router_console_btn)

        # Creates a URL input field
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        # Creates proxy switches. Only one proxy mode can be active at a time.
        self.i2p_proxy_switch = QCheckBox(self.tr_text("use_i2p_proxy"), self)
        self.i2p_proxy_switch.stateChanged.connect(self.toggle_i2p_proxy)
        navbar.addWidget(self.i2p_proxy_switch)

        self.tor_proxy_switch = QCheckBox(self.tr_text("use_tor_proxy"), self)
        self.tor_proxy_switch.stateChanged.connect(self.toggle_tor_proxy)
        navbar.addWidget(self.tor_proxy_switch)

        self.js_switch = QCheckBox(self.tr_text("javascript"), self)
        self.js_switch.stateChanged.connect(self.toggle_javascript)
        navbar.addWidget(self.js_switch)

        self.language_label = QLabel(self.tr_text("language"), self)
        navbar.addWidget(self.language_label)

        self.language_selector = QComboBox(self)
        for language_code, translation in TRANSLATIONS.items():
            self.language_selector.addItem(translation["language_name"], language_code)
        self.language_selector.currentIndexChanged.connect(self.change_language)
        navbar.addWidget(self.language_selector)

        # Creates a status label for proxy
        self.status_label = QLabel(self.tr_text("proxy_status_disabled"), self)
        navbar.addWidget(self.status_label)

        # Connects the URL change signal to update the URL bar
        self.browser.urlChanged.connect(self.update_url)

        # Sets up proxies. I2P is enabled by default.
        self.proxy_mode = "none"
        self.i2p_proxy = QNetworkProxy()
        self.i2p_proxy.setType(QNetworkProxy.HttpProxy)
        self.i2p_proxy.setHostName(I2P_PROXY_HOST)
        self.i2p_proxy.setPort(I2P_PROXY_PORT)

        self.tor_proxy = QNetworkProxy()
        self.tor_proxy.setType(QNetworkProxy.Socks5Proxy)
        self.tor_proxy.setHostName(TOR_PROXY_HOST)
        self.tor_proxy.setPort(TOR_PROXY_PORT)

        # Initialize the NWUrlRequestInterceptor with default headers
        self.request_interceptor = NWUrlRequestInterceptor(self.default_headers())
        profile = self.browser.page().profile()
        if hasattr(profile, "setUrlRequestInterceptor"):
            profile.setUrlRequestInterceptor(self.request_interceptor)
        elif hasattr(profile, "installUrlRequestInterceptor"):
            profile.installUrlRequestInterceptor(self.request_interceptor)

        # Enables I2P proxy initially and set the checkbox state
        self.i2p_proxy_switch.setChecked(True)

        # Enables JavaScript switch by default
        self.js_switch.setChecked(True)

        # Sets the initial URL to local home page
        self.browser.setUrl(QUrl(HOME_PAGE))

    @staticmethod
    def _allow_first_party_cookies_only(request):
        return not request.thirdParty

    def tr_text(self, key):
        return TRANSLATIONS[self.language][key]

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
        self.router_console_btn.setText(self.tr_text("router_console"))
        self.i2p_proxy_switch.setText(self.tr_text("use_i2p_proxy"))
        self.tor_proxy_switch.setText(self.tr_text("use_tor_proxy"))
        self.js_switch.setText(self.tr_text("javascript"))
        self.language_label.setText(self.tr_text("language"))
        self.update_proxy_status()

    def toggle_javascript(self, state):
        enabled = state == Qt.Checked
        self.browser.page().settings().setAttribute(QWebEngineSettings.JavascriptEnabled, enabled)

    def toggle_i2p_proxy(self, state):
        if state == Qt.Checked:
            self._set_proxy_mode("i2p")
        else:
            self._set_proxy_mode("none")

    def toggle_tor_proxy(self, state):
        if state == Qt.Checked:
            self._set_proxy_mode("tor")
        else:
            self._set_proxy_mode("none")

    def _set_proxy_mode(self, mode):
        self.proxy_mode = mode

        if mode == "i2p":
            QNetworkProxy.setApplicationProxy(self.i2p_proxy)
        elif mode == "tor":
            QNetworkProxy.setApplicationProxy(self.tor_proxy)
        else:
            QNetworkProxy.setApplicationProxy(QNetworkProxy())

        self._sync_proxy_switches()
        self.update_proxy_status()

    def _sync_proxy_switches(self):
        self.i2p_proxy_switch.blockSignals(True)
        self.tor_proxy_switch.blockSignals(True)
        self.i2p_proxy_switch.setChecked(self.proxy_mode == "i2p")
        self.tor_proxy_switch.setChecked(self.proxy_mode == "tor")
        self.i2p_proxy_switch.blockSignals(False)
        self.tor_proxy_switch.blockSignals(False)

    def navigate_home(self):
        # Always load the local home page
        self.browser.setUrl(QUrl(HOME_PAGE))

    def navigate_to_url(self):
        url = QUrl.fromUserInput(self.url_bar.text().strip())
        if url.isValid() and not url.isEmpty():
            self.browser.setUrl(url)

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
        page = self.browser.page()
        page.triggerAction(QWebEnginePage.Stop)
        page.history().clear()

        profile = page.profile()
        if hasattr(profile, "clearAllVisitedLinks"):
            profile.clearAllVisitedLinks()

        self.browser.setPage(None)
        page.deleteLater()
        event.accept()


def main():
    app = QApplication(sys.argv)
    QApplication.setApplicationName("I2P Browser")
    app.setWindowIcon(QIcon(str(APP_ICON)))

    window = MainWindow()
    window.showMaximized()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
    

