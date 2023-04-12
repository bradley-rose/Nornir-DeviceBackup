__author__ = "Bradley Rose"
__date__ = "2023/04/11"
__deprecated__ = False
__email__ =  "contact@bradleyrose.co"
__status__ = "Production"
__version__ = "2.0.0"

"""
Actions:
    1. Functions/obtainDynamicHosts.py:
        a) Obtain hosts of the following types from Netbox
            - Switches
            - Routers
            - Firewalls
            - WLCs
            - Voice Gateways
        b) Formats relevant data from the obtained hosts into Inventory/hosts.yaml. Any data presented within staticHosts.yaml takes precedence.
    2. Performs a "show run" (or equivalent for ASAs with virtual contexts).
        a) SSH session is generated with credentials provided in Inventory/defaults.yaml, or if non-standard, Inventory/hosts.yaml. 
        b) These credentials are decrypted with a symmetric encryption key using Functions/decryption.py.
    3. Output the results from the "show run" or equivalent to a text file at "/mnt/configs/" via a global variable.
    4. Performs a "git commit" on each directory (switches, routers, etc.) for version controlling.
"""

"""
*******
Imports
*******
"""

from nornir import InitNornir #Import Nornir
from nornir.core.filter import F #Import Nornir Filtering
from nornir_netmiko import netmiko_send_command #Import Nornir Netmiko
from Functions.decryption import decryptCredentials #Import relative function decryptCredentials
from Functions.obtainDynamicHosts import main as obtainDynamicHosts
from Functions.deviceBackupLog import writeToFile
import git
import datetime

"""
Global Variable Declaration:
"backupDirectory" is a global variable that's used as the parent directory for all of the configuration files.
"""
backupDirectory = "/mnt/configs/"

def asaBackup(firewalls):
    """
    Description
    -----------
    Performs backups on all Cisco ASA firewalls. This also considers ASAs with virtual contexts.

    Parameters
    ----------
    firewalls: Nornir inventory object

    Returns
    -------
    failedDevices: dict
        Blocked: list
            List of devices that were actively blocked from reaching the device.
        Timed Out: list
            List of devices that timed out while trying to access the device. Could be due to an ACL dropped the session, or from the device genuinely being out of service and/or offline.
        Authentication: list
            Bad credentials that need to be resolved.
    """

    def contextBackup(firewalls):
        """
        Description
        -----------
        Backs up ASAs with virtual contexts.
        
        1. Obtains all contexts on the system with a "show context".
        2. For each context, calls "more <filename>" to output the contents of the relevant .cfg file.
        3. Outputs this to a text file in the Firewalls directory.

        Parameters
        ----------
        firewalls: Nornir inventory object containing only Cisco ASAs with virtual contexts ("show mode" returned "multiple")

        Returns
        -------
        None
        """
        def getContexts(task):
            task.run(
                name = "Change to system context",
                task = netmiko_send_command,
                command_string = "changeto system"
            )
            task.run(
                name = "Obtain contexts",
                task = netmiko_send_command,
                command_string = "show context"
            )
        
        def backupContext(task, context):
            task.run(
                name = "Change to system context",
                task = netmiko_send_command,
                command_string = "changeto system"
            )
            task.run(
                name = "Backup context",
                task = netmiko_send_command,
                command_string = "more " + context
            )

        getContextOutput = firewalls.run(
            name = "Obtaining configured contexts",
            task = getContexts
        )

        for device in getContextOutput.keys():
            for output in str(getContextOutput[device][2]).split():
                if "disk0:/" in output:
                    nrDevice = firewalls.filter(name = device)
                    result = nrDevice.run(
                        name = "Backup " + output,
                        task = backupContext,
                        context = output
                    )
                    writeOutput(
                        config = str(result[device][2]).splitlines(),
                        filePath = backupDirectory + "Firewalls/" + device,
                        configFile = "_" + output.split("disk0:/")[1].split(".cfg")[0] + "cfg.txt"
                    )

    """
    Actions:
        1. Identify is a firewall is in "Single" or "Multiple" context mode. 
            a) For multiple context ASAs, this requires multiple .cfg files from disk0:/ to be backed up. This is a different process, and thus, contextBackup() exists for this purpose.
            b) For single context ASAs, this can be run under the same backup process as any other Cisco IOS device that just calls "show run". Backup() exists for this purpose.
        2. Filter the devices, based on the results, into two separate Nornir inventories by adding a temporary group entry. 
            a) If a host returns "Multiple", add the device to the group "Context" for only this runtime. This will be reset next runtime and re-identified.
            b) If a host returns "Single", add it to "ActiveFirewall" just as a way to separate it from the firewalls with context.
        3. Call contextBackup() on the multiple context firewalls, and backup() on the single context firewalls.
    """
    result = firewalls.run(
        name = "Get ASA context mode",
        task = netmiko_send_command,
        command_string = "show mode"
    )

    failedDevices = {"Blocked": [], "Timed Out": [], "Authentication": []}
    for device in result.keys():
        if device in result.failed_hosts:
            if "NoValidConnectionsError" in str(result[device].result):
                failedDevices["Blocked"].append(device)
            elif "Authentication failed" in str(result[device].result):
                failedDevices["Authentication"].append(device)
            else:
                failedDevices["Timed Out"].append(device)
        else:
            mode = result[device][0].result.split()[-1]
            if mode == "single":
                firewalls.inventory.hosts[device].groups.append(firewalls.inventory.groups["ActiveFirewall"])
            elif mode == "multiple":
                firewalls.inventory.hosts[device].groups.append(firewalls.inventory.groups["Context"])
    
    contextHosts = firewalls.filter(F(groups__contains="Context"))
    regularHosts = firewalls.filter(F(groups__contains="ActiveFirewall"))

    regHostShowRun = Backup(regularHosts, "Firewalls")
    contextHostShowRun = Backup(contextHosts, "Firewalls")
    contextBackup(contextHosts)
    
    return failedDevices

def Backup(devices, deviceType):
    """
    Description
    -----------
    Performs a "show run" on all devices contained within the "devices" variable, and stores these to the backupDirectory/deviceType/ directory.

    Parameters
    ----------
    devices: Nornir inventory object 
        Contains devices to be called for show run.
    deviceType: string
        String used for directory name. This is usually "switches", "routers", or other device type groupings.

    Returns
    -------
    failedDevices: dict
        Blocked: list
            List of devices that were actively blocked from reaching the device.
        Timed Out: list
            List of devices that timed out while trying to access the device. Could be due to an ACL dropped the session, or from the device genuinely being out of service and/or offline.
        Authentication: list
            Bad credentials that need to be resolved.
    """
    result = devices.run(
        name="Get Running-Configuration",
        task=netmiko_send_command,
        command_string="show running-config"
    )

    failedDevices = {"Blocked": [], "Timed Out": [], "Authentication": []}
    for device in result.keys():
        if device in result.failed_hosts:
            if "NoValidConnectionsError" in str(result[device].result):
                failedDevices["Blocked"].append(device)
            elif "Authentication failed" in str(result[device].result):
                failedDevices["Authentication"].append(device)
            else:
                failedDevices["Timed Out"].append(device)
        else:
            try:
                writeOutput(
                    config = str(result[device][1]).splitlines(),
                    filePath = backupDirectory + deviceType + "/" + device
                )
            except IndexError:
                writeOutput(
                    config = str(result[device][0]).splitlines(),
                    filePath = backupDirectory + deviceType + "/" + device
                )

    return failedDevices

def writeOutput(*, config, filePath, configFile="_running-config.txt"):
    """
    Description
    -----------
    Writes output from a multi-line string to a text file. Excludes a few lines that would cause version controls without any relevant changes to configurations.

    Parameters
    ----------
    config: multi-line string 
        Contains the configuration contents to be put in the text file.
    filePath: string
        Directory name to store the contents to.
    configFile: string
        Defaults to "_running-config.txt".
        Option for change in the case of multiple context firewalls. (ex. _admincfg.txt)

    Returns
    -------
    None
    """
    excludedLines = (
        ": Written by",
        "!Time:",
        "! Last configuration change",
        "! NVRAM config last updated"
    )

    fileName = filePath + configFile

    with open(fileName, "w") as file:
        for line in config:
            if line.startswith(excludedLines):
                continue
            else:
                file.write(line + "\n") 

def gitCommit(directory):
    """
    Description
    -----------
    Performs a "git commit" on a directory.

    Parameters
    ----------
    directory: string
        Directory name to perform the git commit on.

    Returns
    -------
    gitResult: string
        Results from git commit.
    """
    repo = git.Repo(backupDirectory + directory + '/.git')
    repo.git.add('--all')
    try:
        gitResult = repo.git.commit('-m', "Automated update: " + datetime.datetime.now().replace(microsecond=0).isoformat())
    except git.exc.GitCommandError as e:
        gitResult = e
    return gitResult

def main():
    """
    Description
    -----------
    1. Calls Functions/obtainDynamicHosts.py to pull new hosts from Netbox into Inventory/hosts.yaml.
    2. Calls to Nornir to read Inventory/hosts.yaml and initializes the inventory.
    3. Decrypts all relevant credentials for all hosts.
    4. Backs up, in order:
        a) Firewalls (ASAs)
        b) Switches
        c) Routers
        d) Voice Gateways
        e) WLCs
    5. Performs a git commit in that order after each device in the category is completed.
    6. Calls Functions/deviceBackupLog.py to output failure report to backupResults.html.
    """
    obtainDynamicHosts()

    nr = InitNornir(
        config_file = "config.yaml"
    )
    
    decryptCredentials(nr)

    handler = []; commits = {}

    handler.append(
        asaBackup(
            firewalls = nr.filter(F(groups__contains="Firewalls"))
        )
    )
    commits['Firewalls'] = gitCommit("Firewalls")

    for deviceType in ["Switches", "Routers", "Voice", "WLCs"]:
        handler.append(
            Backup(
                devices = nr.filter(F(groups__contains=deviceType)),
                deviceType = deviceType
            )
        )
        commits[deviceType] = gitCommit(deviceType)

    # Call writeToFile with handler
    failedDevices = {"blocked": [], "timedOut": [], "badAuth": []}
    for dictionary in handler:
        failedDevices['blocked'] += dictionary['Blocked']
        failedDevices['timedOut'] += dictionary['Timed Out']
        failedDevices['badAuth'] += dictionary['Authentication']

    writeToFile(
        blocked = failedDevices['blocked'], 
        timedOut = failedDevices['timedOut'], 
        badAuth = failedDevices['badAuth'], 
        commits = commits
    )

if __name__ == "__main__":
    main()