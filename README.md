# adm4p - AppDomain Manager for Python

When you use PythonNet or other methods to load .Net assemblies into a python script environment, they are loaded into a default domain created by mscorlib without any setup information.  It means you cannot set the target framework name, setup and load an application configuration file, have application base and private bin directories.  

Setting those attributes require creating a non-root applicaiton domain or configuring a default domain at the time of creation.  At the time of creaton of this package, PythonNet team is still working on making non-root domains work.  Luckily, .Net provides an option of configuring a domain (including a default domain) at the time of creation - through a mechanism called AppDomainManager.

This repo provides an implementation based on that mechanism.

## Package details

### Package composition

The package is a single Python module called adm4p (the repo called `adm4p.py` to separate itself from the companion repo with .Net side implementation `adm4p.net` but the module to be referred as `adm4p`).

The package includes a folder with 2 binaries - managed assemblies with AppDomainManager implementation for 32- and 64-bit platforms.

### Preparing for use

Per .Net documentation, assembly implementing referred AppDomainManager must be located in the same directory with the process in which the managed CLR to be loaded.  In Python world that means, the assembly `ADManager4Python.dll` must be copied to the Python installation folder.  Giving sensitive nature of that location, chosing appropriate dll and copying it to Python installation is left for you to do.

Make sure you update that dll after each update of the package.



## Pardon our dust

Building this documentation is a work in progress until it is completed (at which time I will remove this notice).
