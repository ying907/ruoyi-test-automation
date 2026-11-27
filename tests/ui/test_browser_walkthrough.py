import pytest
from playwright.sync_api import sync_playwright

from config.settings import BASE_URL, BROWSERS, LOGIN_PASS, LOGIN_USER
from utils.evidence import Evidence
from utils.redis_helper import get_captcha


def login(page) -> dict:
    """打开登录页，从 Redis 取验证码答案并提交登录，返回现场信息用于诊断。"""
    uuid_box = {"value": None}
    login_resp = {"value": None}

    def on_captcha(response):
        if "/captchaImage" in response.url and response.status == 200:
            uuid_box["value"] = response.json().get("uuid")

    def on_login(response):
        if response.url.endswith("/login") and response.request.method == "POST":
            try:
                login_resp["value"] = f"{response.status} {response.text()[:200]}"
            except Exception as exc:
                login_resp["value"] = f"读取响应失败: {exc}"

    page.on("response", on_captcha)
    page.on("response", on_login)
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1500)

    assert uuid_box["value"], "未捕获到 captchaImage 响应，取不到 uuid"
    code = get_captcha(uuid_box["value"])

    page.locator('input[placeholder*="账号"]').first.fill(LOGIN_USER)
    page.locator('input[placeholder*="密码"]').first.fill(LOGIN_PASS)
    page.locator('input[placeholder*="验证码"]').first.fill(code)
    page.get_by_role("button", name="登").first.click()

    page.wait_for_timeout(1500)
    toast = page.locator(".el-message").all_text_contents()
    page.wait_for_timeout(1500)

    return {"uuid": uuid_box["value"], "code": code, "resp": login_resp["value"], "toast": toast}


@pytest.mark.ui
@pytest.mark.parametrize("channel", BROWSERS)
def test_browser_walkthrough(channel):
    ev = Evidence(channel)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel, headless=True)
        page = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
        ev.attach(page)

        info = login(page)
        if "/login" in page.url:
            pytest.fail(
                f"[{channel}] 登录失败 url={page.url} "
                f"验证码uuid={info['uuid']} 填入答案={info['code']} "
                f"登录响应={info['resp']} 页面提示={info['toast']}"
            )

        ev.screenshot(page, "01_home")

        page.get_by_text("系统管理").first.click()
        page.get_by_text("用户管理").first.click()
        page.wait_for_timeout(1500)
        assert page.locator(".el-table__row").count() > 0, "用户管理列表为空"
        ev.screenshot(page, "02_user")

        page.get_by_text("角色管理").first.click()
        page.wait_for_timeout(1500)
        assert page.locator(".el-table__row").count() > 0, "角色管理列表为空"
        ev.screenshot(page, "03_role")

        browser.close()

    assert ev.ok, f"{channel} 存在前端异常: {ev.summary()}"
