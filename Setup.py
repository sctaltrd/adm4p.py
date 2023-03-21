from setuptools import setup, find_packages

bin_files = []
bin_files.append(r'.\bin\x64\ADManager4Python.dll')
bin_files.append(r'.\bin\x86\ADManager4Python.dll')

setup(name="adm4p",
      version="100.2023.0310",
      packages=["adm4p"],
      package_dir={"adm4p": "."},
      package_data={"adm4p": bin_files},
      include_package_data=True,
      zip_safe=True,
      python_requires='>=3.10',
      )
