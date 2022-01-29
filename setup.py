import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def requirements():
    """Build the requirements list for this project."""
    requirements_list = []

    with open("requirements.txt") as requirements:
        for install in requirements:
            requirements_list.append(install.strip())
    return requirements_list


requirements = requirements()

setuptools.setup(
    name="mailinator-public-api",
    version="0.1.1",
    author="Matheus Fillipe",
    author_email="mattf@tilde.club",
    description="A simple python wrapper for the Public mailinator websockets API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matheusfillipe/mailinator",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications",
        "Topic :: Internet",
    ],
    python_requires=">=3.7",
)
