from dnacentersdk import api as dnacAPI
import Functions.phpipam_API as ipamAPI
from Functions.decryption import decryptAPIuser #Import relative function decryptCredentials
import yaml

def dnacLogin():
    """
    Best practice: 
        1. Generate an API key that ONLY has read access to JUST the inventory. There's no need to grant this automation any additional parts of DNAC.
        2. Encrypt the API key and credential with the symmetric encryption key provided in this directory. Once encrypted, place those below within the quotations.
    """
    dnacUsername, dnacPassword = decryptAPIuser(
        'encryptedDNACusername',
        'encryptedDNACpassword' 
    )

    return (
        dnacAPI.DNACenterAPI(
            base_url = "DNAC URL",
            username = dnacUsername,
            password = dnacPassword,
            verify = False
        )
    )

def ipamLogin():
"""
    Best practice: 
        1. Generate an API key that ONLY has read access to JUST the devices section. There's no need to grant this automation any additional parts of IPAM.
        2. Encrypt the API key and credential with the symmetric encryption key provided in this directory. Once encrypted, place those below within the quotations.
    """
    ipamUsername, ipamPassword = decryptAPIuser(
        'encryptedIPAMusername',
        'encryptedIPAMpassword'
    )

    return (
        ipamAPI.IPAM(
            ipamUsername, 
            ipamPassword, 
            "phpIPAM URL"
        )
    )

def getDnacDevices(dnac,family):
    runOffset = False; offsetVar = 0; allDevices = []
    while True:
        if runOffset:
            offsetVar += 500
            devices = dnac.devices.get_device_list(offset=offsetVar,family=family)
        else:
            devices = dnac.devices.get_device_list(family=family)
        allDevices += devices['response']
        if len(devices['response']) < 500:
            break
        else:
            runOffset = True

    return allDevices

def dnacToStatic(dnacDevices, deviceType, staticHosts):
    for device in dnacDevices:
        shortName = device['hostname'].split(".")[0].lower()
        if shortName in staticHosts.keys():
            if 'hostname' in staticHosts[shortName].keys():
                continue
            else:
                staticHosts[shortName]['hostname'] = device['managementIpAddress']
        else:
            staticHosts[shortName] = {
                "hostname": device['managementIpAddress'],
                "groups": [deviceType]
            }
    return staticHosts

def updateWithDNAC(api, hosts):
    switches = getDnacDevices(api, "Switches and Hubs")
    routers = getDnacDevices(api, "Routers")
    voice = getDnacDevices(api, "Voice")

    hosts = {k.lower(): v for k, v in hosts.items()}
    hosts = dnacToStatic(switches, "Switch", hosts)
    hosts = dnacToStatic(routers, "Router", hosts)
    hosts = dnacToStatic(voice, "Voice", hosts)

    return hosts

def updateWithIPAM(api, hosts):
    devices = api.getDevices()['data']
    for device in devices:
        shortName = device['hostname'].lower()
        if int(device['type']) == 1:
            devType = "Switch"
        elif int(device['type']) == 2:
            devType = "Router"
        elif int(device['type']) == 3:
            devType = "Firewall"
        elif int(device['type']) == 25:
            devType = "Wireless"
        elif int(device['type']) == 15:
            devType = "Voice"
        else:
            continue
        
        if shortName in hosts:
            if 'hostname' in hosts[shortName].keys():
                continue
            else:
                hosts[shortName]['hostname'] = device['ip']
        else:
            hosts[shortName] = {
                "hostname": device['ip'],
                "groups": [devType]
            }
    return hosts

def main():

    dnac = dnacLogin()
    ipam = ipamLogin()

    # Identify static-defined hosts
    with open("Inventory/staticHosts.yaml", "r") as staticHostFile:
        staticHosts = yaml.safe_load(staticHostFile)

    # Update hosts with DNAC hosts. Prioritize static hosts.
    staticHosts = updateWithDNAC(dnac, staticHosts)

    # Update hosts with IPAM hosts. Prioritize static & DNAC hosts.
    staticHosts = updateWithIPAM(ipam, staticHosts)

    with open("Inventory/hosts.yaml", "w") as outputFile:
        yaml.dump(staticHosts, outputFile)

if __name__ == "__main__":
    main()