from setuptools import setup


setup(name="voros",
      version="0.1.4",
      description="scrape MLB pitch API data",
      author="Sam Raker",
      author_email="sam.raker@gmail.com",
      url="https://github.com/swizzard/voros",
      packages=["voros"],
      install_requires=["beautifulsoup4==4.4.1",
                        "lxml==3.6.1",
                        "requests==2.10.0"])
