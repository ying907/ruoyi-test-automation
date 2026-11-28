"""反向/安全用例：未授权访问、伪造 token、SQL 注入、目录穿越回归(DEF-001)。

反向用例的判定思维：不验证"系统能做什么"，验证"系统正确地拒绝了不该做的事"。
"""
import pytest

from utils.api_client import ApiClient


def test_unauthorized_request():
    """无 token 访问业务接口必须被拒（认证层）。

    RuoYi 实现：认证失败 HTTP 层返回 200，业务码 code=401（见 SecurityConfig
    authenticationEntryPoint 的 renderString）。按 HTTP 语义应返回 HTTP 401，
    此处按系统实际契约断言业务码，已记录为规范性观察。
    """
    c = ApiClient()  # 故意不登录
    resp = c.raw("GET", "/system/user/list")
    body = resp.json()
    assert body.get("code") == 401, f"未授权请求应拒绝, 实际 HTTP {resp.status_code} body={body}"


def test_forged_token():
    """伪造 token 必须被拒——不能因为带了 Authorization 头就放行。"""
    c = ApiClient()
    c.session.headers.update({"Authorization": "Bearer forged.token.here"})
    resp = c.raw("GET", "/system/user/list")
    body = resp.json()
    assert body.get("code") == 401, f"伪造 token 应拒绝, 实际 HTTP {resp.status_code} body={body}"


def test_sql_injection_in_query(client):
    """列表查询注入：注入串必须被当字面量处理，查不到数据且不报错。"""
    data = client.get(
        "/system/user/list", params={"userName": "' OR '1'='1", "pageNum": 1, "pageSize": 50}
    )
    assert data["code"] == 200
    assert data["total"] == 0, (
        f"注入串被当 SQL 执行会返回全部用户(total=3)，实际 total={data['total']} —— 已被参数化查询挡住"
    )


def test_sql_injection_in_login():
    """登录接口注入：凭据不存在的注入串必须被拒绝，不能绕过认证。"""
    c = ApiClient()
    with pytest.raises(RuntimeError, match="登录失败"):
        c.login(username="' OR '1'='1' --", password="anything")


def test_directory_traversal_def001(client):
    """DEF-001 回归用例（已知缺陷，预期失败）。

    期望行为：目录穿越请求被拒绝（4xx 或业务错误码）。
    当前实际：拦截生效但异常被静默吞掉，返回空 200 —— 断言失败即缺陷复现。
    修复后移除 xfail 标记，此用例转为正常通过。
    """
    resp = client.raw(
        "GET",
        "/common/download/resource",
        params={"resource": "/profile/../../../../../etc/passwd"},
    )
    rejected = resp.status_code >= 400 or (
        resp.headers.get("Content-Type", "").startswith("application/json")
        and resp.json().get("code") != 200
    )
    assert rejected, (
        f"DEF-001: 目录穿越请求未被拒绝 (status={resp.status_code}, "
        f"content-type={resp.headers.get('Content-Type')})"
    )


test_directory_traversal_def001 = pytest.mark.xfail(
    reason="DEF-001: 异常被静默吞掉返回空 200，缺陷修复前预期失败", strict=False
)(test_directory_traversal_def001)
