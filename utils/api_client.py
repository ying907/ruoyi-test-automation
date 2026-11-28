"""RuoYi 接口客户端：统一会话、token 自动附加、两级业务码统一解析。

用例层只调用 get/post/put/delete，不接触 headers、token、URL 拼接等细节。
"""
import requests

from config.settings import API_BASE_URL, LOGIN_PASS, LOGIN_USER
from utils.redis_helper import get_captcha


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token = None

    def login(self, username: str = LOGIN_USER, password: str = LOGIN_PASS) -> None:
        """取验证码 uuid -> Redis 读答案 -> 登录 -> token 写入会话头。"""
        resp = self.session.get(f"{self.base_url}/captchaImage", timeout=10)
        resp.raise_for_status()
        uuid = resp.json().get("uuid")
        assert uuid, "验证码接口未返回 uuid"

        code = get_captcha(uuid)

        resp = self.session.post(
            f"{self.base_url}/login",
            json={
                "username": username,
                "password": password,
                "code": code,
                "uuid": uuid,
            },
            timeout=10,
        )
        body = resp.json()
        if body.get("code") != 200 or not body.get("token"):
            raise RuntimeError(f"登录失败: {body}")

        self.token = body["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def request(self, method: str, path: str, expect_code: int = 200, **kwargs) -> dict:
        """发请求并统一校验：HTTP 层 raise_for_status，业务层校验 code。

        expect_code 让反向用例复用同一套逻辑：
        正向用例 expect_code=200，注入/越权类用例 expect_code=500。
        """
        resp = self.session.request(method, f"{self.base_url}{path}", timeout=15, **kwargs)
        resp.raise_for_status()

        body = resp.json()
        if body.get("code") != expect_code:
            raise RuntimeError(
                f"{method} {path} 业务码异常: 期望 {expect_code}, 实际 {body}"
            )
        return body

    def raw(self, method: str, path: str, **kwargs) -> requests.Response:
        """逃生舱口：不做解析、不校验业务码，返回原始 Response。

        安全类用例专用：401/注入/目录穿越的响应形态各异（JSON、空体、HTML），
        交给用例自己判定，封装不越权。
        """
        return self.session.request(method, f"{self.base_url}{path}", timeout=15, **kwargs)

    def get(self, path: str, **kwargs) -> dict:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> dict:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> dict:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> dict:
        return self.request("DELETE", path, **kwargs)
