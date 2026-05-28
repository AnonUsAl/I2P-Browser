import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

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
    QLabel,
    QLineEdit,
    QMainWindow,
    QToolBar,
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
        self.setWindowTitle("I2P Browser")

        # Creates a QWebEngineView
        self.browser = QWebEngineView()

        # Creates an off-the-record custom profile.
        self.profile = QWebEngineProfile(self)
        self.profile.setHttpCacheType(QWebEngineProfile.NoCache)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        self.profile.cookieStore().setCookieFilter(self._allow_first_party_cookies_only)

        # Sets the custom profile for the browser
        self.browser.setPage(QWebEnginePage(self.profile, self.browser))

        # Disables JavaScript by default
        settings = self.browser.page().settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, False)
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
        back_btn = QAction('Back', self)
        back_btn.triggered.connect(self.browser.back)
        navbar.addAction(back_btn)

        forward_btn = QAction('Forward', self)
        forward_btn.triggered.connect(self.browser.forward)
        navbar.addAction(forward_btn)

        reload_btn = QAction('Reload', self)
        reload_btn.triggered.connect(self.browser.reload)
        navbar.addAction(reload_btn)

        home_btn = QAction('Home', self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        # Button for I2P Router Console
        custom_redirect_btn = QAction(QIcon(str(APP_ICON)), 'I2P Router Console', self)
        custom_redirect_btn.triggered.connect(self.custom_redirect)
        navbar.addAction(custom_redirect_btn)

        # Creates a URL input field
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        # Creates proxy switches. Only one proxy mode can be active at a time.
        self.i2p_proxy_switch = QCheckBox('Use I2P Proxy', self)
        self.i2p_proxy_switch.stateChanged.connect(self.toggle_i2p_proxy)
        navbar.addWidget(self.i2p_proxy_switch)

        self.tor_proxy_switch = QCheckBox('Use Tor Proxy', self)
        self.tor_proxy_switch.stateChanged.connect(self.toggle_tor_proxy)
        navbar.addWidget(self.tor_proxy_switch)

        # Creates a status label for proxy
        self.status_label = QLabel("Proxy Status: Disabled", self)
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
        default_headers = [
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"),
            ("Accept-Language", "en-US,en;q=0.5"),
            ("Accept-Encoding", "gzip, deflate, br")
        ]
        self.request_interceptor = NWUrlRequestInterceptor(default_headers)
        self.browser.page().profile().setUrlRequestInterceptor(self.request_interceptor)

        # Enables I2P proxy initially and set the checkbox state
        self.i2p_proxy_switch.setChecked(True)

        # Sets the initial URL
        self.browser.setUrl(QUrl(I2P_HOME_URL))

    @staticmethod
    def _allow_first_party_cookies_only(request):
        return not request.thirdParty

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
            self.status_label.setText(f"Proxy Status: I2P {I2P_PROXY_HOST}:{I2P_PROXY_PORT}")
            self.status_label.setStyleSheet("color: green;")
        elif self.proxy_mode == "tor":
            self.status_label.setText(f"Proxy Status: Tor {TOR_PROXY_HOST}:{TOR_PROXY_PORT}")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Proxy Status: Disabled")
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

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
