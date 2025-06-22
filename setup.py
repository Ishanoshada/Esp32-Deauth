from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="esp32-deauth",
    version="0.3.1",
    description="A Python tool for Wi-Fi deauthentication attacks using ESP32 with webserver firmware",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ishan Oshada",
    author_email="ishan.kodtihuwakku.officals@gmail.com",
    url="https://github.com/ishanoshada/esp32-deauth",
    project_urls={
        "Documentation": "https://github.com/ishanoshada/esp32-deauth#readme",
        "Source": "https://github.com/ishanoshada/esp32-deauth",
        "Tracker": "https://github.com/ishanoshada/esp32-deauth/issues",
    },
    license="GPL-2.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "esptool>=4.9.0",
        "requests>=2.28.0",
        "tabulate>=0.9.0",
        "click>=8.0",
        "colorlog"
    ],
    entry_points={
        "console_scripts": [
            "esp32-deauth=esp32_deauth.cli:cli",
        ],
    },
    python_requires=">=3.7",
    keywords="esp32 wifi deauth deauthentication penetration security hacking",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
