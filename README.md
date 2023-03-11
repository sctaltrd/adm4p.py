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

The method `SetupNetFxRuntime` must be called prior of loading any CLR (or triggering any actions that result in loading CLR). Once CLR is loaded, unless you unload a default AppDomain, setting up AppDomainManager will have no affect.

The method sets up the default AppDomain by allowing to configure:
* config file
* primary location of .Net binaries
* target .Net framework name
* default culture for the newly created AppDomain
* rules how to resolve assemblies under this script

```
def SetupNetFxRuntime(
    *, 
    config_file = None, use_config_file_path_as_base = False,
    bin_path = None, use_bin_path_as_base = False, config_file_relative_to_bin = False,
    target_framework = None,   
    culture = None, 
    switches_AR = None, switches_General = None
    ):
```
#### Defaults
By default, ADM4P treats the location of the root script (the script, which is launched with __main__ method) same way as the location of the managed executable - making that location as ApplicationBase directory.  

The ApplicationName property is also set using the name of the root script.

The ADM4P also passes to .Net side (AppDomainManager) current OS working directory.

#### Private binary path

The primary binary path can be either absolute or relative path.  If it is relative path, it is relative to what will be set as the AppDomain's base directory.
The primary binary path can be configured using KEYWORD_LOCATION_CURRENT constant (`$CURRENT$`) - in which case, it is set using current working directory.

If the primary binary path is left blank (or None) or configured with the special constant KEYWORD_LOCATION_BASE (`$BASE$`), the base directory will be used as a location of binaries.

If the binary path is an absolute path, the special flag `use_bin_path_as_base` can be used to set application base directory from the binary path.

More on locating assemblies to load can be found in sections below.

#### Reference to configuration file

The configuration file path can be specified using several ways:
* absolute path to the file (including a config file name)
* relative path to the file (including a config file name); by default, the parent folder is assumed application base, but if the flag `config_file_relative_to_bin` is set to True, the private bin path will be used as a parent folder of the config file path
* just file name - which is an equavalent of ".\<file name>", which means the file located in the directory dedicated for ApplicationBase
* using special constant KEYWORD_CONFIG_DEFAULT (`$DEFAULT$`), which would generate config file name following .Net convention - `<ApplicationName>.config` - assuming the file is located at the ApplicationBase directory.

If the config file path is an absolute path and the flag `use_config_file_path_as_base` is set to True, the path to the configuration file will be used as ApplicationBase directory instead of a location of the root script.

If the parameter is left blank, the config file will not be set for the application domain.

#### Target .Net Framework Name
    
Starting from .Net 4.6.2, Microsoft has introduced compatibility switches to match .Net behavior to behaviors prior of version when it was changed or fixed.  .Net has introduced a class `AppContext`, which is initialized using a target framework name as defined by AppDomain.  If AppDomain has target framework name left blank, the behavior of .Net 4.0 (and prior) is assumed.
    
During setting up of runtime, the target framework can be passed using several ways:
* specified in the following format (per .Net's FrameworkName class): `<identifier>, Version=[v|V]<version>` aka `.NETFramework,Version=v4.8.0`
* blank
* using special constant KEYWORD_TGTFRM_STARTUP (`$STARTUP$`)
    
Blank will invoke the built-in logic inside ADM4P implementation: since the Python.exe is not managed process and does not contain .Net assembly manifest, it cannot be treated as entry assembly; and target framework attribute of any loaded assemblies cannot be used since references to assemblies are loaded in pretty much random order and way after AppDomain is created; and unfortunately supportedRuntime element in the startup section of the config file is not used by .Net by default and we avoid using it either as a default option (even when config file is provided) since inside AppDomainManager code we are limited only to what is defined inside mscorlib.
    
If using `<supportedRuntime>`'s `sku` attribute is desired, the target framework has to be specified using KEYWORD_TGTFRM_STARTUP constant.
    
Note: Compatibility switches can be overriden inside `<runtime>` section if the target framework name is recognized as new version but the application must run using older / legacy behavior. But since the approach based on AppDomainManager ignores `<runtime>` section of the configuration file assigned to the run (see section below), maintaining accurate target framework name is important.
    
#### Culture

The desired culture can be set using standard culture notation. 

The culture is not set to AppDomain - AppDomain's setup does not require that parameter.  The culture is assigned to `CultureInfo.DefaultThreadCurrentCulture', which makes all threads inside the curernt AppDomain run inside that culture.  

Besides a useful shortcut, setting up domain threads with the sapecific culture addsto more robust assembly resolution.

The current implementation of ADM4P does not manage UI culture.

#### Switches

Switches (AR or General) are ULONG (unsigned 64-bit integers).  

AR stands for "assembly resolution" and described in sections below.

General switches are reserved and currently not used.

### Assembly resolution switches

Switches that control assembly resolution logic are described under .Net considerations.

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

### Culture

Please consult .Net documentation on how culture assigned to threads works across domains.

### Limitations: `<runtime>` section

Managed subsystems of .Net are all initialized after domain creation.  Therefore all facilities and all configuration sections work with one notable exception: `<runtime>`.  The CLR runtime components are loaded and prepared for execution before mscorlib (which is a managed assembly) even loaded - in the unmanaged code of CLR host. Which is a bummer - nothing in the AppDomain manager's code can reconfigure any runtime components (including GC).

Configuring such switches (such as `gcAllowVeryLargeObjects`) are required in the config file that is associated with the process, inside which the CLR is loaded.  In our case, the process is python.exe, and the expected config file name is `python.exec.config`.

As a consolation, only `<runtime>` section needs to be defined in that "global" config file.  Any sections defined in python.exe.config file will be effectively ignored once the configuration file for the AppDomain is provided.

### python.exe.config in the role of machine.config

The globally defined python.exe.config file could act similarly to machine.config or applicationHost.config files (normally present with IIS hosting). As an added benefit along these lines, GC setting switches are ignored inside machine.config but ARE considered inside our de-facto machine level setup, which python,exe.config may become - from the hack to be a valuable player in the maintaining working environment. So dedicating python.exe.config to global runtime switches sounds less of the hack for me (than using that file for script specific configuration).

## Pardon our dust

Building this documentation is a work in progress until it is completed (at which time I will remove this notice).
