# Device Backup Usage Guide

- [Device Backup Usage Guide](#device-backup-usage-guide)
  - [File Structure](#file-structure)
  - [General Information](#general-information)
- [Usage Instructions for Device Backups](#usage-instructions-for-device-backups)
  - [What happens once `deviceBackup.py` is called?](#what-happens-once-devicebackuppy-is-called)
  - [How does `deviceBackup.py` know what devices to backup?](#how-does-devicebackuppy-know-what-devices-to-backup)
  - [Where does `deviceBackup.py` store the running-configuration files?](#where-does-devicebackuppy-store-the-running-configuration-files)

## File Structure
```
Nornir
│   README.md
│   README.html
│   config.yaml  
│   deviceBackup.py 
│   ...    
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
│   │   
```

## General Information
This "Device Backup" script is built using the "Nornir" framework. For more information on how this works, including the inventory and variable inheritance structure, [here's a link to the developer's official documentation](https://nornir.readthedocs.io/en/latest/). I wouldn't recommend this for *light* reading as it's quite complicated unless you know Python and have time to dissect this code against the documentation.

## What happens once `deviceBackup.py` is called?
- Open `deviceBackup.py` in a text editor. 
- Each action is broken up into an independent function. 
  - `getConfig` intakes a group of devices, establishes an SSH session, calls `more system:running-config` in the CLI, stores the outputs to a variable, and then closes the SSH session.
    - This is performed using [Netmiko](https://pypi.org/project/nornir-netmiko/).
  - `Backup` calls the `getConfig` with the appropriate devices and then formats the output of the running-configuration to a text file. **This function also integrates version control on the text files** by calling `git commit` on each of the appropriate directories for Firewalls, Switches, Routers, etc. This ensures that we can take daily copies of each running configuration, but we **only store the changes**, meaning we aren't storing hundreds of copies of each network device, but rather only the changes of each device as it varies from its previous copy. If one line of the configuration changed from the previous day, only that single line is updated, not an entirely new text file.
  - `main` calls the `Backup` and `contextBackup` functions as needed. It filters for the appropriate devices and calls the applicable function.
## How does `deviceBackup.py` know what devices to backup?
- These files are hierarchical, meaning that if a variable exists within multiple files, the variable within `hosts.yaml` will take priority over that same variable listed in `groups.yaml`, which will take priority over that same variable listed in `defaults.yaml`. 
  - `hosts.yaml` contains information about each host, including its IP address, groups it belongs to for filtering, and optionally an encrypted username/password combination if it does not use TACACS+/RADIUS/LDAP. If a device is to be added to the backup script, simply add in the relevant information here and save the file, and that's it.
  - `groups.yaml` contains group-specific variables. For example, each firewall uses the "cisco_asa" platform instead of the "cisco_ios" platform, and as such this is listed here.
  - `defaults.yaml` contains default variables that apply in all cases when no more specific variables are listed in the other two files. Listed here are encrypted TACACS+/LDAP credentials used to log into the vast majority of the network appliances, as well as the platform and port for Netmiko to use when SSH-ing into the devices.
## Where does `deviceBackup.py` store the running-configuration files?
- The running-configurations get stored to:
> `\\path\to\backups`.
- These directories are all version controlled. Open a `Powershell` window and navigate to the `Configs` directory as mentioned in the previous bullet, and then further navigate into the directory you'd like to explore. 
Example: 
```ps1 
cd "\\path\to\backups\directory"
```
- To view all versions available of the entire directory:  
```ps1
# After you enter this command, take note of the 7-character hex values provided with each version.
git log --oneline
```
- To view the differences between the most current version **of the entire directory** and a previous version:
```ps1
git diff <hex value>
```

- To view the differences between the most current verison **of a specific file** and a previous version: 
```ps1
# Method 1:
git diff <hex value>:<filename>

# Method 2:
git show -1 <filename> # One revision prior to current
git show -2 <filename> # Two revisions prior to current.
```

- To obtain a text file of a previous version of a file: 
  - `outputFilename` is the full path and filename of where you'd like to output the contents to. 
```ps1
`git cat-file -p <hex value>:<filename> <outputFilename>
```
  
Example: 
```ps1
git cat-file -p abc1234:fileName.txt > C:\Users\<User>\Desktop\fileName_old.txt
```