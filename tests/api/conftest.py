"""tests/api 的共享 fixture：所有接口用例从这里拿登录态。"""
import pytest

from utils.api_client import ApiClient
from utils.redis_helper import delete_pwd_counter


@pytest.fixture
def client() -> ApiClient:
    """每个用例一个已登录的客户端（函数级作用域，用例之间互不共享状态）。"""
    c = ApiClient()
    c.login()
    return c


@pytest.fixture
def admin_lock_guard():
    """保护 admin 账号不被错误密码计数锁死。

    yield 之前 = 准备（无）；yield 之后 = 拆卸（teardown），
    无论用例成败都会执行 DEL，计数器永远到不了 5。
    """
    yield
    delete_pwd_counter("admin")
