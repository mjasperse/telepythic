from setuptools import setup
setup(
    name = "telepythic",
    version = "1.5",
    packages = [ 'telepythic', 'telepythic.library' ],
    package_dir = { 'telepythic':'' },
    package_data = { 'telepythic': ['LICENSE.txt','README.md'] },
    
    # metadata for upload to PyPI
    author = "Martijn Jasperse",
    author_email = "m.jasperse@gmail.com",
    license = "BSD",
    description = "A python library for communicating with test equipment and measurement devices",
    long_description = "This library is for communicating with measurement and test-equipment using text-based VISA (e.g. GPIB-like) or telnet interfaces. Its intended purpose is to simplify writing scripts to control equipment and download measurements, in an interface-agnostic way.",
    keywords = "GPIB VISA comms test equipment measurement devices",
    url = "https://bitbucket.org/martijnj/telepythic",
)
