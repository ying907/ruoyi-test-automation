"""登录接口用例：正向 + 反向。"""
import pytest

from utils.api_client import ApiClient


def test_login_success(client):
    """登录成功后 token 可用，且能查到登录用户身份（数据回查）。"""
    assert client.token, "登录后 token 为空"

    info = client.get("/getInfo")
    assert info["user"]["userName"] == "admin", f"登录身份异常: {info['user']}"


def test_login_wrong_password(admin_lock_guard):
    """错误密码必须被拒绝，且 token 不得被写入会话（对比 Postman 污染 token 的坑）。"""
    c = ApiClient()
    with pytest.raises(RuntimeError, match="登录失败"):
        c.login(password="deliberately-wrong-123")

    assert c.token is None, "登录失败后 token 竟然有值，会话状态被污染"
