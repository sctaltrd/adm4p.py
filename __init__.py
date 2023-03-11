#
# Copyright (c) 2023, SCT Alternative Inc.
# Copyright (c) 2023, Vadim Katsman
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by SCT Alternative and Vadim Katsman.
# 4. Neither the name of SCT Alternative, Vadim Katsman nor the
#    names of their contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE 
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import os
import sys
import xml.etree.ElementTree as xmltree
import __main__

ADM4P_ADM_ASM_NM = "ADManager4Python"
ADM4P_ADM_ASM_VER = "100.2023.310"
ADM4P_ADM_TYP = 'ADM4P.ADManager4Python'
ADM4P_ENV_VAR = 'ADM_4_PYTHON_ACTIVATION_CONTEXT'
NET_ADM_TP_VAR = 'APPDOMAIN_MANAGER_TYPE'
NET_ADM_ASM_VAR = 'APPDOMAIN_MANAGER_ASM'

SWITCH_AR_CONSIDERREQUESTINGASM = 0x0000000000000001
SWITCH_AR_WORKINGDIR            = 0x0000000000000002
SWITCH_AR_ACTIVATIONWORKINGDIR  = 0x0000000000000004
SWITCH_AR_LOADEDASMS            = 0x0000000000000008
SWITCH_AR_SUBFOLDERS            = 0x0000000000000010
SWITCH_AR_ALLENABLED            = 0xFFFFFFFFFFFFFFFF

KEYWORD_LOCATION_BASE    = '$BASE$'
KEYWORD_LOCATION_CURRENT = '$CURRENT$'
KEYWORD_LOCATION_BIN     = '$BIN$'
KEYWORD_CONFIG_DEFAULT   = '$DEFAULT$'
KEYWORD_TGTFRM_STARTUP   = '$STARTUP$'

# .Net activation context is a pipe-delimited list in the following order:
# - working (OS current) directory
# - location of the script with the main function (defines AppDomain.BaseDirectory)
# - name of the module with the main function (will be used for default config file name and AppDomain.SetupInformation.ApplicationName property)
# - location of .Net binaries specified by developer via enhanced set_runtime (developers can always do what they are doing now - inject path to PATH environment variable)
#   * specified location (absolute or relative to base path - the location of the top script)
#   * $CURRENT$ - use OS current directory for the execuring process
#   * blank or $BASE$ - AppDomain.BaseDirectory will be used
#   NOTE: bin path can be set as a AppBase directory (if left blank)
# - configuration file path or $DEFAULT$ (to indicate configuration file name is bujilt in ./Net style - <module name>.config - and located together with the root script) (defaulot is blank - no config required):
#   * full path to a configuration file
#   * path relative to the config root location (by default it is a ApplicationBase but can be also a Bin path)
#   * just file name (equavalent to .\name - follows same rules as relative path)
#   * $DEFAULT$ - config file generated following .Net convention (we can generate all of this inside python code as we have access to way more APIs than inside AppDomainManager)
#   * blank - not specified / not requested
#   NOTE: if config file path is absolute path, it can be used as a source for the base directory 
# - target .Net Framework
#   * specified
#   * blank - will inherit the TargetFrameworkName from mscorlib (which would correspond to the .Net version in which the code will be executed)
#   NOTE: since the Python.exe is not managed process and does not contain .Net assembly manifest, it cannot be treated as entry assembly;
#         and target framework attribute of any loaded assemblies cannot be used since references to assemblies are loaded in pretty much random order and way after AppDomain is created;
#         and unfortunately supportedRuntime element in the startup section of the config file is not used by .Net by default and
#         we avoid using it either (even when config file is provided) since inside AppDomainManager code we are limited only to what is defined inside mscorlib 
#   * $STARTUP$ - will use config's supported runtime element of the startup section as input (ignored if config file is not requested)
#   NOTE: while we cannot use it inside managed code, we still can load config file as XML inside python code while preparing the activation context
#   NOTE: the target framework name must be in the following format (per .Net's FrameworkName class): <identifier>, Version=[v|V]<version> aka .NETFramework,Version=v4.8.0 
# - culture that will be set as a default culture for AppDomain threads
# - switches_AR: unsigned long value of binary switches that regulate the logic of searching for the assembly binaries (if blank, the AppDomain manager will include all features as it will default to 0xFFFFFFFFFFFFFFFF
# - switches_General: reserved collection of unsigned long value of binary switches currently not used and defaulted by AppDomain manager to 0
def SetupNetFxRuntime(
    *, 
    config_file = None, use_config_file_path_as_base = False,
    bin_path = None, use_bin_path_as_base = False, config_file_relative_to_bin = False,
    target_framework = None,   
    culture = None, 
    switches_AR = None, switches_General = None
    ):
    # validate the existence of the ADM4PN assembly in Python installation directory (potential CRC validation for added measure of security)
    manager_dll_path = os.path.join(os.path.dirname(sys.executable), ADM4P_ADM_ASM_NM + ".dll")
    if not os.path.exists(manager_dll_path):
        raise Exception(f"The expected assembly {ADM4P_ADM_ASM_NM} is not found in Python installation path at {os.path.dirname(sys.executable)}")
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
    constTgtFramework = 5
    constCulture = 6
    constSwitchesAR = 7
    constSwitchesGeneral = 8
    
    # key locations
    context_elements.append(os.getcwd())
    mainScript = __main__.__file__
    context_elements.append(os.path.dirname(mainScript))
    context_elements.append(os.path.basename(mainScript))

    # binary path
    if bin_path is None:
        bin_path = ''
    if len(bin_path) > 0:
        if bin_path == KEYWORD_LOCATION_CURRENT:
            bin_path = context_elements[constWorkingDir]
        elif bin_path == KEYWORD_LOCATION_BASE:
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
        if config_file == KEYWORD_CONFIG_DEFAULT:
            config_file = mainScript + ".config"
        else:
            if not is_config_file_abs:
                config_root = context_elements[constBaseDir]
                if config_file_relative_to_bin and len(bin_path) > 0:
                    config_root = context_elements[constBinPath]
                config_file = os.path.abspath(
                    os.path.join(config_root,config_file)
                    )
            else:
                if use_config_file_path_as_base:
                    context_elements[constBaseDir] = os.path.dirname(config_file)
    context_elements.append(config_file)
    
    # target framework
    if target_framework is None:
        target_framework = ''
    if len(target_framework) > 0:
        if target_framework == KEYWORD_TGTFRM_STARTUP:
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

    # culture
    context_elements.append('' if culture is None else culture) 
    
    # switches AR (switches will be always at the end)
    context_elements.append('' if switches_AR is None else f'{switches_AR}') 
    # switches general (switches will be always at the end)
    context_elements.append('' if switches_General is None else f'{switches_General}') 

    os.environ[NET_ADM_TP_VAR] = ADM4P_ADM_TYP
    os.environ[NET_ADM_ASM_VAR] = f'{ADM4P_ADM_ASM_NM}, Version={ADM4P_ADM_ASM_VER}'
    os.environ[ADM4P_ENV_VAR] = '|'.join(context_elements)

def LoadNetFxRuntime():
    import pythonnet
    pythonnet.load("netfx")

# usage example 
if __name__ == "__main__":
    import ctypes
    
    SetupNetFxRuntime(config_file = KEYWORD_CONFIG_DEFAULT, bin_path = KEYWORD_LOCATION_CURRENT, target_framework = KEYWORD_TGTFRM_STARTUP)
    loaderAssembly = r'D:\_WorkRoot\Global\Python\adm4p\adm4p.net\_Tests\ExportedAssembly\bin\x64\Debug\ExportedAssembly.dll'
    tlc = ctypes.CDLL(loaderAssembly)
    tlc.tlc_BringItUp()

