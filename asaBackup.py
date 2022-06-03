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
    Gets running-config via SSH using Netmiko for standard ASAs.

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

def main():
    """
    Description
    -----------
    Primary commands executed when asaBackup is called. Aims to backup all ASAs, both with and without contexts, to a remote directory.

    Parameters
    ----------
    None

    Returns
    -------
    Text files to a backup directory.
    """

    # Initializes Nornir, decrypts device credentials.
    nr = InitNornir(config_file="config.yaml")
    ASA2130s = nr.filter(F(groups__contains='ASA2130'))
    decryptCredentials(ASA2130s)

    #Obtain `more system:running-config` from standard ASAs.
    result = ASA2130s.run(
        name="Getting Configs",
        task=getConfig
    )

    # Store Outputs to File
    # Of note, because this is on a Windows machine, file locations require a backslash + an escape backslash.
    backupDirectory = "\\\\Directory\\To\\Store\\Backups\\"

    """
    For each device, the goal is to write the output to a file, and then run a `git commit` on the directory.
    If no changes are necessary, the `git commit` will fail - which is intended.
    The only time a git commit will not fail is when an update has occurred on the running configuration.
    """

    for device in result.keys():
        if device in result.failed_hosts:
            print_result(device)
        else:
            with open(backupDirectory + device + '_running-config.txt', 'w') as file:
                textToWrite = str(result[device][1]).splitlines()
                for line in textToWrite:
                    if line.startswith(": Written by"):
                        continue
                    else:
                        file.write(line + "\n")

    # Git library stages all potential changes, and then tries to commit.
    # It does assume that you've already initialized the Git directory with `git init .`.
    # If there are no changes, the commit will fail with an error message stating that everything is up-to-date.
    # If there are changes, if completes the commit with the timestamped message as seen below.

    repo = git.Repo(backupDirectory + '.git')
    repo.git.add('--all')
    try:
        print(repo.git.commit('-m', "Automated update: " + datetime.datetime.now().replace(microsecond=0).isoformat()))
    except git.exc.GitCommandError as e:
        print(e)
    
if __name__ == '__main__':
    main()