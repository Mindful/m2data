import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="m2data",
    version="0.0.11",
    author="Joshua Tanner",
    author_email="mindful.jt@gmail.com",
    description="A package for reading .m2 files commonly used in GEC tasks",
    keywords=['grammatical error correction',  'GEC', 'natural langauge processing'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mindful/m2data",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
)