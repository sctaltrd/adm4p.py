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

## API

### SetupNetFxRuntime

### Assembly resolution switches

Switches that control assembly resolution logic are described in the section below (under .Net considerations).

### LoadNetFxRuntime shortcut

## .Net considerations

### Companion repository
The .Net implementation of AppDomainManager is published using a companion repository [adm4p.net](https://github.com/sctaltrd/adm4p.net).

### Assembly resolution logic and switches

### Limitations: `<runtime>` section

Managed subsystems of .Net are all initialized after domain creation.  Therefore all facilities and all configuration sections work with one notable exception: `<runtime>`.  The CLR runtime components are loaded and prepared for execution before mscorlib (which is a managed assembly) even loaded - in the unmanaged code of CLR host. Which is a bummer - nothing in the AppDomain manager's code can reconfigure any runtime components (including GC).

Configuring such switches (such as `gcAllowVeryLargeObjects`) are required in the config file that is associated with the process, inside which the CLR is loaded.  In our case, the process is python.exe, and the expected config file name is `python.exec.config`.

As a consolation, only `<runtime>` section needs to be defined in that "global" config file.  Any sections defined in python.exe.config file will be effectively ignored once the configuration file for the AppDomain is provided.

### python.exe.config in the role of machine.config

The globally defined python.exe.config file could act similarly to machine.config or applicationHost.config files (normally present with IIS hosting). As an added benefit along these lines, GC setting switches are ignored inside machine.config but ARE considered inside our de-facto machine level setup, which python,exe.config may become - from the hack to be a valuable player in the maintaining working environment. So dedicating python.exe.config to global runtime switches sounds less of the hack for me (than using that file for script specific configuration).

## Pardon our dust

Building this documentation is a work in progress until it is completed (at which time I will remove this notice).
