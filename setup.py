from setuptools import setup, find_packages

setup(
    name="LogFileMonitor",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "watchfiles"
        "OperaPowerRelay @ git+https://github.com/OperavonderVollmer/OperaPowerRelay.git@v1.1.4"
    ],
    python_requires=">=3.7",
    author="Opera von der Vollmer",
    description="Monitor log files for changes",
    url="https://github.com/OperavonderVollmer/LogFileMonitor", 
    license="MIT",
)
