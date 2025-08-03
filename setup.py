"""
LocalCtrl 安装配置
"""
from setuptools import setup, find_packages

setup(
    name="localctrl",
    version="0.1.0",
    description="An open-source remote control service with plugin support",
    author="LocalCtrl Team",
    author_email="",
    url="",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "sqlalchemy>=1.4.23",
        "pydantic>=1.8.2",
        "python-jose[cryptography]>=3.3.0",
        "werkzeug>=2.0.1",  # 用于密码哈希
        "psutil>=5.8.0",    # 用于系统信息
        "python-multipart",  # 用于表单处理
        "email-validator",  # 用于邮箱验证
    ],
    entry_points={
        "console_scripts": [
            "localctrl=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
