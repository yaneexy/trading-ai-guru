from setuptools import setup, find_packages

setup(
    name="trading_ai_guru",
    version="0.1",
    packages=find_packages(),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.115.5",
        "uvicorn>=0.32.1",
        "websockets>=11.0.3",
        "python-dotenv>=1.0.0",
        "pandas>=2.1.3",
        "numpy>=1.26.2",
        "xrpl-py>=3.0.0",
        "python-socketio>=5.4.0",
        "aiohttp>=3.8.1",
        "httpx>=0.24.1",
        "ccxt>=4.4.35"
    ],
)
