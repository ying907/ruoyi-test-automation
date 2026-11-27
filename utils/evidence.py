from config.settings import EVIDENCE_DIR


class Evidence:
    """收集一次浏览器走查的全部异常证据，并统一给出判定。"""

    def __init__(self, tag: str):
        self.tag = tag
        self.console_errors = []
        self.page_errors = []
        self.failed_requests = []
        self.bad_responses = []

    def attach(self, page):
        page.on("console", self._on_console)
        page.on("pageerror", self._on_page_error)
        page.on("requestfailed", self._on_request_failed)
        page.on("response", self._on_response)

    def _on_console(self, msg):
        if msg.type == "error":
            self.console_errors.append(msg.text)

    def _on_page_error(self, error):
        self.page_errors.append(str(error))

    def _on_request_failed(self, request):
        self.failed_requests.append(f"{request.url} :: {request.failure}")

    def _on_response(self, response):
        if response.status >= 400:
            self.bad_responses.append(f"{response.status} {response.url}")

    def screenshot(self, page, name: str):
        path = EVIDENCE_DIR / f"{self.tag}_{name}.png"
        page.screenshot(path=str(path))
        return path

    @property
    def ok(self) -> bool:
        return not (
            self.console_errors
            or self.page_errors
            or self.failed_requests
            or self.bad_responses
        )

    def summary(self) -> dict:
        return {
            "console_errors": self.console_errors,
            "page_errors": self.page_errors,
            "failed_requests": self.failed_requests,
            "bad_responses": self.bad_responses,
        }
