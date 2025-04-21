import logging
import pytest

def pytest_configure(config):
    """设置pytest日志捕获"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    """测试开始前的钩子函数"""
    yield
    # 启用对stdout/stderr的捕获
    if hasattr(item, "_capture_manager"):
        item._capture_manager.set_capture(True)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """测试运行时的钩子函数"""
    yield
    # 确保捕获已启用
    if hasattr(item, "_capture_manager"):
        item._capture_manager.set_capture(True) 