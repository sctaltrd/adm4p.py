from setuptools import setup, find_packages
packages = []
packages.append("adm4p")
setup(name="adm4p",
      version="100.2023.0310",
      packages=packages,
      package_dir={"adm4p": "../adm4p"},
      include_package_data=True,
      python_requires='>=3.10',
      )
