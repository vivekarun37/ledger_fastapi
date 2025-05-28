from setuptools import setup, find_packages

setup(
    name="jitfarm_api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "motor",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "httpx"
    ]
) 