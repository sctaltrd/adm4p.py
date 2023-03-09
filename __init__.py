import os
import sys
import xml.etree.ElementTree as xmltree
import __main__
import pythonnet

# .Net activation context as pipe-delimited list in the following order:
# - working (OS current) directory
# - location of the script with the main function (defines AppDomain.BaseDirectory)
# - name of the module with the main function (will be used for default config file name and AppDomain.SetupInformation.ApplicationName)
# - location of .Net binaries specified by developer via enhanced set_runtime (developers can always do what they are doing now - inject path to PATH environment variable)
#   * specified location (absolute or relative to base path - the location of the top script)
#   * $CURRENT$ - use OS current directory for the execuring process
#   * blank or $BASE$ - AppDomain.BaseDirectory will be used
# - configuration file path or $DEFAULT$ (to indicate configuration file name is bujilt in ./Net style - <module name>.config - and located together with the root script) (defaulot is blank - no config required):
#   * full path to a configuration file
#   * path relative to the location of the top script
#   * just file name (equavalent to .\name)
#   * $DEFAULT$ - config file generated following .Net convention (we can generate all of this inside python code as we have access to way more APIs than inside AppDomainManager)
#   * $BIN$ - use bin path for config file path
#   * blank - not specified / not requested
#   NOTE: configuration file is specified via set_runtime parameter
# - target .Net Framework
#   * specified
#   * blamk - will inherit the TargetFrameworkName from mscorlib (which would correspond to the .Net version in which the code will be executed)
#   NOTE: since the Python.exe is not managed process and does not contain .Net assembly manifest, it cannot be treted as entry assembly;
#         and target framework attribute of any loaded assemblies cannot be used sicne references to assemblies are loaded in pretty much random order and way after AppDomain is created;
#         and unfortunately supportedRuntime element in the startup section of the config file is not used by .Net by default and
#         we avoid using it either (even when config file is provided) since inside AppDomainManager code we are limited only to what is defined inside mscorlib (pretty much System namespace and that's it)
#   * $STARTUP$ - will use config's supported runtime element of the startup section as input (ignored if config file is not requested)
#   NOTE: while we cannot use it inside managed code, we still can load config file as XML inside python code while preparing the activation context
#   NOTE: the target framework name must be in the following format (per .Net's FrameworkName class): <identifier>, Version=[v|V]<version> aka .NETFramework,Version=v4.8.0 
def SetupNetFxRuntime(config_file = None, bin_path = None, target_framework = None, use_config_file_path_as_base = False, use_bin_path_as_base = False):
    # validate the existence of the ADM4PN assembly in Python installation directory (potential CRC validation for added measure of security)
    adManagerAssemblyName = "ADManager4Python"
    adManagerVersion = "100.2023.308"
    adManagerType = 'ADM4P.ADManager4Python'
    manager_dll_path = os.path.join(os.path.dirname(sys.executable), adManagerAssemblyName + ".dll")
    if not os.path.exists(manager_dll_path):
        raise Exception(f"The expected assembly {adManagerAssemblyName} is not found in Python installation path at {os.path.dirname(sys.executable)}")
    else:
        # TODO: additional validation if possible:
        # - verification of file validity
        # - verification of authenticity
        # - verification of assembly version matching required version above
        pass
    
    # setup code
    context_elements = []
    
    constWorkingDir = 0
    constBaseDir = 1
    constAppName = 2
    constBinPath = 3
    constCfgFile = 4
    constTgtFramework = 6
    
    # key locations
    context_elements.append(os.getcwd())
    mainScript = __main__.__file__
    context_elements.append(os.path.dirname(mainScript))
    context_elements.append(os.path.basename(mainScript))

    # binary path
    if bin_path is None:
        bin_path = ''
    if len(bin_path) > 0:
        if bin_path == '$CURRENT$':
            bin_path = context_elements[constWorkingDir]
        elif bin_path == '$BASE$':
            bin_path = context_elements[constBaseDir]
        elif os.path.isabs(bin_path):
            if use_bin_path_as_base:
                context_elements[constBaseDir] = bin_path
        else:
            bin_path = os.path.abspath(
                os.path.join(context_elements[constBaseDir],bin_path)
                )
    context_elements.append(bin_path)
    
    # config file
    is_config_file_abs = False
    if config_file is None:
        config_file = ''
    if len(config_file) > 0:
        is_config_file_abs = os.path.isabs(config_file)
        if config_file == '$DEFAULT$':
            config_file = mainScript + ".config"
        else:
            if not(is_config_file_abs):
                config_file = os.path.abspath(
                    os.path.join(context_elements[constBaseDir],config_file)
                    )
            else:
                if use_config_file_path_as_base:
                    context_elements[constBaseDir] = os.path.dirname(config_file)
    context_elements.append(config_file)
    
    # target framework
    if target_framework is None:
        target_framework = ''
    if len(target_framework) > 0:
        if target_framework == '$STARTUP$':
            target_framework = ''
            if len(config_file) > 0:
                try:
                    root = xmltree.parse(config_file).getroot()
                    runtime = root.find(".//startup/supportedRuntime")
                    if runtime is not None:
                        target_framework = runtime.attrib['sku']
                except Exception as error:
                    #print(f"{error}")
                    pass
    context_elements.append(target_framework)

    os.environ['APPDOMAIN_MANAGER_TYPE'] = adManagerType
    os.environ['APPDOMAIN_MANAGER_ASM'] = f'{adManagerAssemblyName}, Version={adManagerVersion}'
    os.environ['ADM_4_PYTHON_ACTIVATION_CONTEXT'] = '|'.join(context_elements)

def LoadNetFxRuntime():
    pythonnet.load("netfx")

# usage example 
if __name__ == "__main__":
    import ctypes
    
    SetupNetFxRuntime(config_file = '$DEFAULT$', bin_path = '$CURRENT$', target_framework = '$STARTUP$')
    loaderAssembly = r'D:\_WorkRoot\Global\Python\adm4p\adm4p.net\_Tests\ExportedAssembly\bin\x64\Debug\ExportedAssembly.dll'
    tlc = ctypes.CDLL(loaderAssembly)
    tlc.tlc_BringItUp()

