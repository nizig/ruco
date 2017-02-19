from setuptools import setup

setup(
  name="ruco",
  packages=["ruco"],
  version="0.6",
  description="Rust (by Facepunch Studios) rcon API and shell utility",
  author="exo",
  author_email="exo@eckso.io",
  url="https://github.com/nizig/ruco",
  download_url="https://github.com/nizig/ruco/tarball/release-0.6",
  zip_safe=False,
  entry_points={
    "console_scripts": ["ruco=ruco.cli:main"],
  },
  install_requires=[
    "PyYAML",
    "click",
    "pytz",
    "tabulate",
    "tzlocal",
    "websocket-client",
  ],
  keywords=["rust", "rcon", "game", "console", "facepunch"],
  classifiers=[],
)
