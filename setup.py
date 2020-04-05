from setuptools import find_packages, setup

if __name__ == '__main__':
    with open("README.md", "r", encoding='utf8') as fh:
        long_description = fh.read()

    setup(
        name='tesseractor',
        packages=find_packages(),
        version='0.1.0',
        description='',
        author='Gijs Peters',
        long_description=long_description,
        long_description_content_type="text/markdown",
        classifiers=[
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
        ],
    )
