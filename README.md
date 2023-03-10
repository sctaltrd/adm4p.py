# adm4p - AppDomain Manager for Python

When you use PythonNet or other methods to load .Net assemblies into a python script environment, they are loaded into a default domain created by mscorlib without any setup information.  It means you cannot set the target framework name, setup and load an application configuration file, have application base and private bin directories.  

Setting those attributes requires creating a non-root applicaiton domain or configuring a default domain at the time of creation.  At the time of creaton of this package, PythonNet team is still working on making non-root domains work.  Luckily, .Net provides an option of configuring a domain (including a default domain) at the time of creation - through a mechanism called AppDomainManager.

This repo provides an implementation based on that mechanism.

## Package details

### Package composition

The package is a single Python module called adm4p (the repo called `adm4p.py` to separate itself from the companion repo with .Net side implementation `adm4p.net` but the module to be referred as `adm4p`).

The package includes a folder with 2 binaries - managed assemblies with AppDomainManager implementation for 32- and 64-bit platforms.

### Installing a package

You can install a package directly from this repository:

```
pip install adm4p @ git+https://github.com/sctaltrd/adm4p.py
```

### Preparing for use

Per .Net documentation, assembly implementing referred AppDomainManager must be located in the same directory with the process in which the managed CLR to be loaded.  In Python world that means, the assembly `ADManager4Python.dll` must be copied to the Python installation folder.  Giving sensitive nature of that location, chosing appropriate dll and copying it to Python installation is left for you to do.

Make sure you update that dll after each update of the package.

## API

### SetupNetFxRuntime

### Assembly resolution switches

Switches that control assembly resolution logic are described in the section below (under .Net considerations).

### LoadNetFxRuntime shortcut

Technically, this package provides ability to configure a default domain for any scenario of CLR hosting and is totally independent from PythonNet.  But in practice, chances are PythonNet is the de-facto choice of working with managed code from python scripts.  To recognize that, the simple shortcut to load a `netfx` runtime (.Net Framework) is offered for consolidated API:
```
def LoadNetFxRuntime():
    import pythonnet
    pythonnet.load("netfx")
```
`pythonnet` module is imported inside the method to break a dependency on the PythonNet while importing `adm4p` module.

It goes without saying that you cannot load PythonNet's runtime prior of setting up parameters for the AppDomainManager to use when ClrLoader is invoked.  This is why this shortcut method provides an added consistency:
```
import adm4p
adm4p.SetupNetFxRuntime(*args)
adm4p.LoadNetFxRuntime()
```

When using PythonNet we import clr module to load assemblies.  But importing pythonnet directly in the script could be replaced with importing adm4p instead.

But it is optional at the same time - consider example of not using PythonNet in the first place:
```
import ctypes
import adm4p
adm4p.SetupNetFxRuntime(config_file = adm4p.KEYWORD_CONFIG_DEFAULT, bin_path = adm4p.KEYWORD_LOCATION_CURRENT, target_framework = adm4p.KEYWORD_TGTFRM_STARTUP)
loaderAssembly = r'D:\_WorkRoot\Global\Python\adm4p\adm4p.net\_Tests\ExportedAssembly\bin\x64\Debug\ExportedAssembly.dll'
tlc = ctypes.CDLL(loaderAssembly)
tlc.tlc_BringItUp()
```
In the example above, the test assembly exports a public method of the class same way PythonNet's ClrLoader does - using "DllExport" attribute from NXPorts.

NOTE: By introducing this wrapper, we are not trying to replace PythonNet with ADM4P branding.  The scope of adm4p module is limited to configure the default AppDomain and is not expected to expand.  PythonNet is given a full credit for the great solution provided to a community.

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
