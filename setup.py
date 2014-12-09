from setuptools import setup, find_packages
setup(
    name = "telepythic",
    version = "1.0",
    packages = find_packages(),
    
    package_data = {
        '': ['*.txt','*.md']
    },
    
    # metadata for upload to PyPI
    author = "Martijn Jasperse",
    author_email = "m.jasperse@gmail.com",
    description = "A python library for communicating with test equipment and measurement devices",
    license = "BSD",
    keywords = "GPIB VISA comms test equipment measurement devices",
    url = "https://bitbucket.org/martijnj/telepythic",

    # could also include long_description, download_url, classifiers, etc.
)
