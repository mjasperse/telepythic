from setuptools import setup
setup(
    name = "telepythic",
    version = "1.1",
    packages = [ 'telepythic', 'telepythic.library' ],
    package_dir = { 'telepythic':'' },
    package_data = { '': ['*.txt','*.md'] },
    
    # metadata for upload to PyPI
    author = "Martijn Jasperse",
    author_email = "m.jasperse@gmail.com",
    description = "A python library for communicating with test equipment and measurement devices",
    long_description = "This library is for communicating with measurement and test-equipment using text-based VISA (e.g. GPIB-like) or telnet interfaces. Its intended purpose is to simplify writing scripts to control equipment and download measurements, in an interface-agnostic way.",
    license = "BSD",
    keywords = "GPIB VISA comms test equipment measurement devices",
    url = "https://bitbucket.org/martijnj/telepythic",

    # could also include long_description, download_url, classifiers, etc.
)
