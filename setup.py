from setuptools import setup

setup(
    name="ruco",
    version="0.1",
    description="Library and utility for using the Rust game server console",
    author="exo",
    author_email="exo@eckso.io",
    url="https://github.com/nizig/ruco",
    download_url="https://github.com/nizig/ruco/tarball/0.1",
    packages=["ruco"],
    zip_safe=False,
    entry_points={
        "console_scripts": ["ruco=ruco.cli:main"],
    },
    install_requires=[
        "PyYAML",
        "click",
        "tabulate",
        "websocket-client",
    ],
    keywords=["rust", "rcon", "game", "console"],
    classifiers=[],
)
