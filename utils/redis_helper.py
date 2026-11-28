import subprocess

from config.settings import REDIS_CLI


def delete_pwd_counter(username: str) -> None:
    """删除登录错误密码计数器，防止测试把账号锁死。"""
    result = subprocess.run(
        [REDIS_CLI, "DEL", f"pwd_err_cnt:{username}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"清除计数器失败: {result.stderr.strip()}")


def get_captcha(uuid: str) -> str:
    """从 Redis 读取验证码答案。注意：值带双引号，必须 strip 掉。"""
    result = subprocess.run(
        [REDIS_CLI, "GET", f"captcha_codes:{uuid}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"读取 Redis 失败: {result.stderr.strip()}")
    return result.stdout.strip().strip('"')
