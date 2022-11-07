"""
Actions:
    1. Targets a Nornir inventory of network devices; 
    2. Obtains the running configuration of the devices; 
    3. Outputs the running configurations to a remote directory organized by device type; and
    4. Performs a `git commit` on these directories
"""

__author__ = "Bradley Rose"
__date__ = "2022/11/07"
__deprecated__ = False
__status__ = "Production"
__version__ = "1.0.0"

from nornir import InitNornir #Import Nornir
from nornir.core.filter import F #Import Nornir Filtering
from nornir_netmiko import netmiko_send_command #Import Nornir Netmiko
from Functions.decryption import decryptCredentials #Import relative function decryptCredentials
from Functions.obtainDynamicHosts import main as obtainDynamicHosts
from Functions.sendEmail import sendEmail
import git
import datetime

# Store the configuration files outputs to this parent directory:
backupDirectory = "/mnt/configs/"

def getConfigContext(task):
    """
    Description
    -----------
    Gets running-config via SSH using Netmiko for ASAs with an admin context.

    Parameters
    ----------
    task: Task
        Nornir Task object containing devices to run against.

    Returns
    -------
    results: Nornir Object
        You can choose to call print_object against the results, or manipulate them with Python commands as you will.
    
    Example
    ------- 
    for device in results:
        print(str(results[device][2]).splitlines())
        print(str(results[device][3]).splitlines())
    
    Example
    -------
    for device in results:
        print_result(results[device])
    """

    task.run(
        name="Changing to System Context",
        task=netmiko_send_command,
        command_string="changeto context system"
    )

    task.run(
        name="Show Admin Context Configuration",
        task=netmiko_send_command,
        command_string="more disk0:/admin.cfg"
    )

    task.run(
        name="Show Running-Configuration",
        task=netmiko_send_command,
        command_string="more system:running-config"
    )

def contextBackup(ASA2130s):
    """
    Description
    -----------
    Backup function for ASA 2130s with context. 
        1. Takes the devices post-filter from the Nornir inventory
        2. Calls the getConfigContext function on those devices
        3. Passes the output to writeOutput for writing to a file (x2 for admin context and system context)

    Parameters
    ----------
    ASA2130s: object (Nornir)
        Nornir object containing a tree-structured representation of the target devices.

    Returns
    -------
    failedDevices: dict
        Blocked: List
            list of devices actively blocking connection via SSH. Firewall or local policy.
        Timed Out: List
            list of devices that timed out connection. 
    """
    result = ASA2130s.run(
        name="Getting Configs on ASAs with Context",
        task=getConfigContext
    )

    failedDevices = {"Blocked": [], "Timed Out": [], "Authentication": []}
    for device in result.keys():
        if device in result.failed_hosts:
            if "NoValidConnectionsError" in str(result[device][1].result):
                failedDevices["Blocked"].append(device)
            elif "Authentication failed" in str(result[device][1].result):
                failedDevices["Authentication"].append(device)
            else:
                failedDevices["Timed Out"].append(device)
        else:
            writeOutput(
                runningConfig = str(result[device][2]).splitlines(),
                filePath = backupDirectory + "Firewalls/" + device,
                isASA2130 = True
            )

            writeOutput(
                runningConfig = str(result[device][3]).splitlines(),
                filePath = backupDirectory + "Firewalls/" + device
            )

    return failedDevices

def Backup(devices, deviceType, gitCommit=True):

    """
    Description
    -----------
    Primary backup function. 
        1. Takes the devices post-filter from the Nornir inventory
        2. Calls the getConfig function on those devices
        3. Passes the output to writeOutput for writing to a file
        4. (default) Performs a `git commit` on the output directory.

    Parameters
    ----------
    devices: object (Nornir)
        Nornir object containing a tree-structured representation of the target devices.
    deviceType: string
        A string representing the directory name for the backup. "Switches", "Firewalls", etc. 
    gitCommit: boolean
        if gitCommit = True:
            Performs a `git commit` on the target directory.
        else:
            Ignores git.

    Returns
    -------
    failedDevices: dict
        Blocked: List
            list of devices actively blocking connection via SSH. Firewall or local policy.
        Timed Out: List
            list of devices that timed out connection. 
    """

    #Obtain `more system:running-config` from switches.
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
                    runningConfig = str(result[device][1]).splitlines(),
                    filePath = backupDirectory + deviceType + "/" + device
                )
            except IndexError:
                writeOutput(
                    runningConfig = str(result[device][0]).splitlines(),
                    filePath = backupDirectory + deviceType + "/" + device
                )

    if gitCommit:
        repo = git.Repo(backupDirectory + deviceType + '/.git')
        repo.git.add('--all')
        try:
            gitResult = repo.git.commit('-m', "Automated update: " + datetime.datetime.now().replace(microsecond=0).isoformat())
        except git.exc.GitCommandError as e:
            gitResult = e

        return failedDevices, gitResult

    return failedDevices, ""

def writeOutput(runningConfig, filePath, isASA2130=False):
    """
    Description
    -----------
    Writes running-config output to a file on a remote directory.

    Parameters
    ----------
    runningConfig: string
        Multi-line string containing contents of running-configuration
    filePath: string
        The destination filePath for the output.
    isASA2130: boolean
        if isASA2130 = True:
            filePath.endswith("_disk0-admincfg.txt")
        else:
            filePath.endswith("_running-config.txt")

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

    if isASA2130:
        fileName = filePath + "_disk0-admincfg.txt"
    else:
        fileName = filePath + "_running-config.txt"

    with open(fileName, "w") as file:
        for line in runningConfig:
            if line.startswith(excludedLines):
                continue
            else:
                file.write(line + "\n") 

def main():
    """
    Description
    -----------
    Primary commands executed when deviceBackup.py is called. Backs up all devices to a remote directory.

    Parameters
    ----------
    None

    Returns
    -------
    Text files to the mount point at /mnt/configs/ 
    """

    # Calls obtainDynamicHosts to retrieve hosts from DNAC and phpIPAM
    obtainDynamicHosts()

    # Initializes Nornir, decrypts device credentials.
    nr = InitNornir(config_file="config.yaml")

    # Decrypt credentials of all devices in scope
    decryptCredentials(nr)
    
    # Initialize handler for failed devices
    handler = []; commits = {}

    # Call Backup on ASA 2130s with contexts
    handler.append(
        contextBackup(
            ASA2130s = nr.filter(F(groups__contains='ASA_Context'))
        )
    )

    # Call Backup on remaining ASAs/firewall objects
    allFirewalls = nr.filter(F(groups__contains="Firewall"))
    handle, commits['Firewalls'] = Backup(
        devices = allFirewalls.filter(~F(groups__contains="ASA_Context")),
        deviceType = "Firewalls"
    )
    handler.append(handle)

    # Call Backup on Nexus Devices.
    # gitCommit = False because more switches are yet to be backed up. 
    handle, x = (
        Backup(
            devices = nr.filter(F(groups__contains="Nexus")),
            deviceType = "Switches",
            gitCommit = False
        )
    )
    handler.append(handle)

    # Call Backup on Switch objects
    # gitCommit all switches, including the previous Nexus switches.
    handle, commits['Switches'] = Backup(
        devices = nr.filter(F(groups__contains="Switch")),
        deviceType = "Switches"
    )
    handler.append(handle)

    # Call Backup on Router objects
    handle, commits['Routers'] = Backup(
        devices = nr.filter(F(groups__contains="Router")),
        deviceType = "Routers"
    )
    handler.append(handle)

    # Call Backup on Voice Gateways
    handle, commits['Voice'] = Backup(
        devices = nr.filter(F(groups__contains="Voice")),
        deviceType = "Voice Gateways"
    )
    handler.append(handle)

    # Call Backup on WLCs
    handle, commits['Wireless'] = Backup(
        devices = nr.filter(F(groups__contains="Wireless")),
        deviceType = "WLCs"
    )
    handler.append(handle)

    # Call sendEmail_FailedHosts with handler
    failedDevices = {"blocked": [], "timedOut": [], "badAuth": []}
    for dictionary in handler:
        failedDevices['blocked'] += dictionary['Blocked']
        failedDevices['timedOut'] += dictionary['Timed Out']
        failedDevices['badAuth'] += dictionary['Authentication']


    sendEmail(failedDevices['blocked'], failedDevices['timedOut'], failedDevices['badAuth'], commits)
    
if __name__ == '__main__':
    main()