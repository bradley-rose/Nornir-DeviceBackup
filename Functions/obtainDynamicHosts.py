import yaml
import pynetbox

def main():
    # Use Pynetbox to filter for various roles
    nb = pynetbox.api(
        "https://<Netbox URL>",
        "<Netbox API Key>"
    )

    switches = nb.dcim.devices.filter(
        has_primary_ip = True,
        platform_id = 1,
        role_id = 1,
        # Role_id and platform_id must match your Netbox environment.
        status = "active"
    )
    routers = nb.dcim.devices.filter(
        has_primary_ip = True,
        platform_id = 1, 
        role_id = 2,
        # Role_id and platform_id must match your Netbox environment.
        status = "active"
    )

    # Identify static-defined hosts
    with open("Inventory/staticHosts.yaml", "r") as staticHostFile:
        hosts = yaml.safe_load(staticHostFile)

    count = 1
    for category in [switches, routers]:
        for device in category:
            shortName = device.name.lower()

            if not shortName in hosts:
                hosts[shortName] = {}
            else:
                pass
        
            hosts[shortName]['hostname'] = device.primary_ip.address.split("/")[0]
            if count == 2:
                cat = "Switches"
            elif count == 3:
                cat = "Routers"

            hosts[shortName]['groups'] = [cat]
        count += 1

    with open("Inventory/hosts.yaml", "w") as outputFile:
        yaml.dump(hosts, outputFile)

if __name__ == "__main__":
    main()