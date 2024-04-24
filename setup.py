# pylint:disable=missing-module-docstring
import setuptools

with open("README.md") as fp: # pylint:disable=unspecified-encoding
    long_description = fp.read()

setuptools.setup(
    name="django-password-expire",
    version="4.2.1",
    description="Django app for forcing password expiration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jayceeit/django-password-expire",
    author="JC Consulting",
    author_email="itadmin@jvcwaters.com",
    license="BSD",
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=["humanize"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Framework :: Django",
    ]
)
