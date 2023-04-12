# Device Backup Usage Guide

- [Device Backup Usage Guide](#device-backup-usage-guide)
  - [File Structure](#file-structure)
  - [General Information](#general-information)
- [Usage Instructions for Device Backups](#usage-instructions-for-device-backups)
  - [What happens once `deviceBackup.py` is called?](#what-happens-once-devicebackuppy-is-called)
  - [How are credentials provided?](#how-are-credentials-provided)
  - [Config / Backup Management](#config--backup-management)

## File Structure
```
Network Device Backup
├── Inventory
│   ├── defaults.py
│   ├── groups.py
│   ├── hosts.py
│   └── staticHosts.py
├── Functions
│   ├── __init__.py
│   ├── decryption.py
│   ├── deviceBackupLog.txt
│   ├── Hosts Encryption Key.txt
│   └── obtainDynamicHosts.py
├── config.yaml
├── deviceBackup.py 
├── requirements.txt
├── README.md 
└── .gitignore
```

## General Information
This "Device Backup" script is built using [Nornir](https://nornir.readthedocs.io/en/latest/) for the automation framework and [Netbox](https://docs.netbox.dev/en/stable/) as the inventory system.

# Usage Instructions for Device Backups
`deviceBackup.py` should be called from a cronjob on a Linux server that's executed on a regular interval.

```sh
* 5 * * * cd /scripts/Backup && python /scripts/Backup/deviceBackup.py > runtimeLog.txt 2>&1
```

## What happens once `deviceBackup.py` is called?
### Summary
1. Identifies all hosts (statically defined, Netbox)
2. SSH's into each device, performs a `show run`
3. Outputs the result to a text file on a remote directory
4. Performs a `git commit` to version control the directory.

### Details
1. Calls upon `Functions/obtainDynamicHosts.py`, which obtains hosts from Netbox and formats the hosts into a YAML-formatted file for the rest of the script to rely upon:
   1. Reads in `Inventory/staticHosts.yaml`. These are statically defined hosts that require special handling. These hosts and their associated properties take the highest priority. Reasons to include a host in the static file may include:
      1. Non-standard credentials (local auth)
      2. Non-standard device sub-type (Switch (IOS/IOS-XE vs. Nexus Switch (NXOS))
   2. Calls to Netbox based on what's defined in `obtainDynamicHosts.py`. You, as the user, will have to define this operation as it pertains to your Netbox environment. Have a read through the [Pynetbox readthedocs](https://readthedocs.org/projects/pynetbox/) for some guidance.
2. Initializes the Nornir framework. This reads in the recently created `Inventory/hosts.yaml` file containing the hosts identified in the previous step.
3. Decrypts any provided credentials with `Functions/decryption.py` and `Functions/Hosts Encryption Key.txt`.
4. Log into each device via SSH using the Netmiko framework. 
   1. My devices don't have HTTP enabled on them as of yet, so NAPALM and other API-based automation frameworks are out of the picture.
   2. Netmiko is an automation framework that utilizes SSH for its actions.
5. Calls a `show run` as appropriate for each type of device.
6. Outputs the result to a text file at `/mnt/configs/`, which is an SMB/CIFS-mountpoint for the enterprise file store where my configs live.
7. Performs a `git commit` on all relevant directories to version control the backups.

## How are credentials provided?
- The `config.yaml` file highlights three pieces of information:
  - The location of the `hosts.yaml` file, which is the file that would contain all host information after the dynamic inventory is completed.
  - `groups.yaml` contains group-specific variables. For example, each firewall uses the `cisco_asa` platform instead of the `cisco_ios` platform, and as such this is listed here to allow Nornir to differentiate the proper context for logging in via SSH, translating `show run` to the appropriate syntax for the OS, etc.
  - `defaults.yaml` contains default variables that apply in all cases when no more specific variables are listed in the other two files. Listed here are encrypted TACACS+/LDAP credentials for `svcnetops` used to log into the vast majority of the network appliances, as well as the the default `cisco_ios` platform and SSH port 22 for Netmiko to use when SSH-ing into the devices.

## Config / Backup Management
- The running-configurations get stored to a git-tracked directory at the mount-point at `/mnt/configs/`.