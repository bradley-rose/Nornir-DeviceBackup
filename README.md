# Nornir Usage Guide
Nornir is a Python-based automation framework. I've been using this for certain aspects of network automation for a few reasons: 
- Ansible requires installation on a Linux box of some form, and it's significantly slower and more difficult to work with as it doesn't use Python.
- Nornir is able to use APIs where available, and then fallback to SSH (using Netmiko) when APIs aren't an option. 

# Initial Configuration

## File Structure
```
Nornir
│   README.md
│   README.html
│   config.yaml    
│   runBook1.py   
│   runBook2.py   
│   runBook3.py   
│
└───Inventory
│   │   hosts.yaml
│   │   groups.yaml
│   │   defaults.yaml 
│   │   
└───Functions
│   │   __init__.py
│   │   decryption.py
│   │   Hosts Encryption Key.txt 
```

## General Information
Nornir has an inheritance structure for variables when it comes to host/inventory management. Variables take effect in order of the following priority:  
1. hosts.yaml
2. groups.yaml
3. defaults.yaml

You can have the same variable listed in all three locations. For example, a group of hosts may share a username variable, but one of these hosts may have a unique username while the rest would use the generic one. The `username` variable listed on each host within `hosts.yaml` would take precedence over the `username` variable listed in `groups.yaml`.

## config.yaml
```yaml
---
inventory:
  plugin: SimpleInventory
  options:
    host_file: "Inventory/hosts.yaml"
    group_file: "Inventory/groups.yaml"
    defaults_file: "Inventory/defaults.yaml"
logging:
  enabled: False
```

## hosts.yaml
- Everything after the hostname is optional for each host.
- The hostname variable can contain an IP address or a DNS-resolvable name.

```yaml
---
hostA:
  hostname: '192.168.0.1'
  groups:
    - 'Cisco_IOS'

hostB: 
  hostname: '192.168.0.2'
  groups:
    - 'Cisco_ASA'
  username: 'aUsernameGoesHere'
  password: 'aPasswordGoesHere'
```

## groups.yaml
This is the file in which you would specify variables that impact groups of hosts.
- The platform variables are based off of [Netmiko's supported platforms](https://github.com/ktbyers/netmiko/blob/develop/PLATFORMS.md). 
- This can also be based on [NAPALM](https://napalm.readthedocs.io/en/latest/support/), BUT this relies on RESTCONF/NETCONF, which again, isn't an option for the devices I work with in many cases.

```yaml
---
Cisco_IOS:
  username: 'aDifferentUsernameGoesHere'
  password: 'aDifferentPasswordGoesHere'
  platform: cisco_ios

Cisco_ASA:
  platform: cisco_asa
```

## defaults.yaml
This is the defaults file, where variables can be set as a *last-resort* type. If a variable has not yet been set to impact a host within either the `hosts.yaml` file, or the `groups.yaml` file on a group that the host belongs to, then these variables will be active.

```yaml
---
port: 22
```

# Using Nornir
Here's an example file that pulls the running-configuration from a group of devices in the hosts file, stores the outputs to a text file, and version controls/updates them with Git. This uses Netmiko, but similar functionality could be built for NAPALM if you have REST APIs configured. Or, alternatively, you could just call the APIs into Nornir as well. This example just takes the easy/old route with SSH/CLI.

```py
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
    backupDirectory = "<\\\\Directory\\To\\Store\\Backups\\"

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
```