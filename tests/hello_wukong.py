#!/usr/bin/env python3
"""
Hello Wukong - 悟空工作流演示文件

这是一个演示 Wukong 2.0 工作流的示例文件。
由斗战胜佛分身创建。
"""

import unittest


def hello_wukong(name: str = "World") -> str:
    """返回问候语"""
    return f"Hello, {name}! 悟空就绪!"


class TestHelloWukong(unittest.TestCase):
    """Hello Wukong 测试"""

    def test_default_greeting(self):
        """测试默认问候"""
        result = hello_wukong()
        self.assertEqual(result, "Hello, World! 悟空就绪!")

    def test_custom_name(self):
        """测试自定义名称"""
        result = hello_wukong("Wukong")
        self.assertEqual(result, "Hello, Wukong! 悟空就绪!")


if __name__ == "__main__":
    # 独立运行时输出问候
    print(hello_wukong("Wukong 2.0"))
    print("\n运行测试...")
    unittest.main(verbosity=2)
