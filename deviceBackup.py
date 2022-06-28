from nornir import InitNornir #Import Nornir
from nornir.core.filter import F #Import Nornir Filtering
from nornir_netmiko import netmiko_send_command #Import Nornir Netmiko
from nornir_utils.plugins.functions import print_result
from Functions.decryption import decryptCredentials #Import relative function decryptCredentials
import git
import datetime

def getConfig(task):
    """
    Description
    -----------
    Gets running-config via SSH using Netmiko for Cisco IOS devices.

    Parameters
    ----------
    task: Task
        Nornir Task object containing devices to run against.

    Returns
    -------
    results: Nornir Object
        You can choose to call print_object against the results, or manipulate them with Python commands as you will.

        for device in results:
            print(results[device][1])
    """
    task.run(
        name="Get Running-Configuration",
        task=netmiko_send_command,
        command_string="more system:running-config"
    )

def Backup(devices, directory, gitCommit=True):
    decryptCredentials(devices)

    backupDirectory = "" + directory + "\\"

    #Obtain `more system:running-config` from devices.
    result = devices.run(
        name="Getting Configs",
        task=getConfig
    )

    """
    For each device, the goal is to write the output to a file, and then run a `git commit` on the directory.
    If no changes are necessary, the `git commit` will fail - which is intended.
    The only time a git commit will not fail is when an update has occurred on the running configuration.
    """

    for device in result.keys():
        if device in result.failed_hosts:
            print_result(device)
            continue
        else:
            with open(backupDirectory + device + '_running-config.txt', 'w') as file:
                textToWrite = str(result[device][1]).splitlines()
                for line in textToWrite:
                    if line.startswith(": Written by"):
                        continue
                    else:
                        file.write(line + "\n")

    if gitCommit:
        repo = git.Repo(backupDirectory + '.git')
        repo.git.add('--all')
        try:
            print(repo.git.commit('-m', "Automated update: " + datetime.datetime.now().replace(microsecond=0).isoformat()))
        except git.exc.GitCommandError as e:
            print(e)

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
    Text files to the following location: 
        <Insert backup directory here>
    """

    # Initializes Nornir, decrypts device credentials.
    nr = InitNornir(config_file="config.yaml")

    # Call Backup on remaining ASAs/firewall objects
    allFirewalls = nr.filter(F(groups__contains="Firewall"))

    # Call Backup on Switch objects
    Backup(nr.filter(F(groups__contains="Switch")), "Switches")

    # Call Backup on Router objects
    Backup(nr.filter(F(groups__contains="Router")), "Routers")
    
if __name__ == '__main__':
    main()