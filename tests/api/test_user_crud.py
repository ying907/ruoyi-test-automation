"""用户管理 CRUD 链式用例：新增 -> 查询确认 -> 修改 -> 删除 -> 回查。

设计要点：
- 一条链在一个函数里（一个场景 = 一条用例，失败可按步骤注释定位）
- 用户名带时间戳，天然唯一、可重复运行（幂等）
- cleanup fixture 保证链在任意一步断掉后，测试用户都会被清掉（零残留）
"""
import time

import pytest

TEST_USER = f"tauto_{int(time.time())}"


@pytest.fixture
def cleanup_test_user(client):
    """后置钩子：按用户名查询并删除测试用户，失败也执行。"""
    yield
    rows = client.get(
        f"/system/user/list?pageNum=1&pageSize=50&userName={TEST_USER}"
    ).get("rows", [])
    for row in rows:
        client.delete(f"/system/user/{row['userId']}")


def test_user_crud_chain(client, cleanup_test_user):
    # ---- 1. 新增 ----
    client.post(
        "/system/user",
        json={
            "userName": TEST_USER,
            "nickName": "自动化测试用户",
            "password": "Test@12345",
            "deptId": 100,
            "roleIds": [2],
            "postIds": [],
            "status": "0",
            "remark": "接口自动化链式用例创建",
        },
    )

    # ---- 2. 查询确认：写进去的数据真的落库了 ----
    rows = client.get(
        f"/system/user/list?pageNum=1&pageSize=50&userName={TEST_USER}"
    )["rows"]
    assert len(rows) == 1, f"新增后应能查到且仅 1 条，实际 {len(rows)}"
    user_id = rows[0]["userId"]

    # ---- 3. 修改：状态真的变更了 ----
    client.put(
        "/system/user",
        json={
            "userId": user_id,
            "userName": TEST_USER,
            "nickName": "自动化-已修改",
            "deptId": 100,
            "roleIds": [2],
            "postIds": [],
            "status": "0",
        },
    )
    detail = client.get(f"/system/user/{user_id}")["data"]
    assert detail["nickName"] == "自动化-已修改", (
        f"修改后回查 nickName 应为'自动化-已修改'，实际 {detail['nickName']}"
    )

    # ---- 4. 删除 ----
    client.delete(f"/system/user/{user_id}")

    # ---- 5. 回查：删干净了 ----
    rows = client.get(
        f"/system/user/list?pageNum=1&pageSize=50&userName={TEST_USER}"
    )["rows"]
    assert len(rows) == 0, f"删除后回查应无数据，实际还剩 {len(rows)} 条"
