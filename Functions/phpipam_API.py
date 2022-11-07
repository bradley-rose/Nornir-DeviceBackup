#!/usr/bin/env Python
__author__ = "Bradley Rose"
__version__ = "0.1"
"""
Please see usage details in the readme provided!
This API was built using the provided API documentation.
  https://phpipam.net/api/api_documentation/
"""

import requests
import json

# Disable requests' warnings for insecure connections
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class IPAM:
    def __init__(self,apiUser,token,phpIPAMurl):
        self.token = token
        self.apiUser = apiUser
        self.urlBase = phpIPAMurl + "/api/" + apiUser + "/"

    """
    --------------------------
    | HTTP Standard Requests |
    --------------------------
    These are the basic GET, POST, PUT, and DELETE used for CRUD.
    These are used by other methods defined beneath these to perform operations.
    """

    def get(self, url):
        """
        Description
        -----------
        HTTP GET operations on a provided URL.

        Parameters
        ----------
        url: string
            A provided URL string for a particular resource.

        Returns
        -------
        If HTTP status code == 200:
            data: dictionary
                Dictionary of key:value pairs of all attributes of resource where GET operation was performed.
        else:
            message: string
                An IPAM error message.
        """
        request = requests.get(url, verify=False, headers={'token':self.token})

        if request.status_code == 200:
            return request.json()
        else:
            return request.status_code

    def patch(self, url, payload):
        """
        Description
        -----------
        HTTP PUT operations on a provided URL.
        Used to UPDATE EXISTING data.

        Parameters
        ----------
        url: string
            A provided URL string for a particular resource.
        payload: dictionary
            key:value pairs for the particular resource.

        Returns
        -------
        result: int
            HTTP status code
        """
        payload = json.dumps(payload, indent = 4)
        result = requests.patch(url, data=payload, verify=False, headers={'token':self.token, "Content-Type": "application/json"}).status_code
        return result

    def put(self, url, payload):
        """
        Description
        -----------
        HTTP PUT operations on a provided URL.
        Used to UPDATE EXISTING data.

        Parameters
        ----------
        url: string
            A provided URL string for a particular resource.
        payload: dictionary
            key:value pairs for the particular resource.

        Returns
        -------
        result: int
            HTTP status code
        """
        payload = json.dumps(payload, indent = 4)
        result = requests.put(url, data=payload, verify=False, headers={'token':self.token}).status_code
        return result

    def post(self, url, payload):
        """
        Description
        -----------
        HTTP POST operations on a provided URL.
        Used to ADD NEW data.

        Parameters
        ----------
        url: string
            A provided URL string for a particular resource.
        payload: dictionary
            key:value pairs for the particular resource.

        Returns
        -------
        result: int
            HTTP status code
        """
        result = requests.post(url, json=payload, verify=False, headers={'token':self.token}).json()
        return result

    def delete(self,url):
        """
        Description
        -----------
        HTTP DELETE operations on a provided URL.
        Used to ADD NEW data.

        Parameters
        ----------
        url: string
            A provided URL string for a particular resource.

        Returns
        -------
        result: int
            HTTP status code
        """
        result = requests.delete(url, verify=False, headers={'token':self.token}).status_code
        return result

    """
    ------------------
    | CUSTOM METHODS |
    ------------------
    These are custom methods that utilize the above well-defined HTTP methods to perform operations.
    """

    def getUserSession(self):
        """
        Description
        -----------
        Checking user + token against phpIPAM for validity.

        Parameters
        ----------
        None

        Returns
        -------
        HTTP status code
        """
        url = self.urlBase + "user/"
        results = self.get(url)
        return results

    def getSubnets(self, specific=False):
        """
        Description
        -----------
        Obtains subnet objects from phpIPAM.

        Parameters
        ----------
        (optional) specific: string
            A CIDR formatted (w.x.y.z/ab) subnet.

        Returns
        -------
        if specific=False:
            result: dictionary
                Obtains ALL subnets within the entirety of phpIPAM.
        else:
            results: dictionary
                Obtains one specific subnet object and its key:value attributes.
        """
        url = self.urlBase + 'subnets'
        if specific:
            url += '/cidr/' + specific
        results = self.get(url)
        return results

    def getSubnetsBySection(self, sectionId):
        """
        Description
        -----------
        Obtains subnet objects from a specific section. 

        Parameters
        ----------
        section: int
            Obtains all subnets within section referenced by phpIPAM ID.
        
        Returns
        -------
        result: dictionary
            Dictionary object containing the identified subnets.
        """
        url = self.urlBase + "/sections/" + str(sectionId) + "/subnets"
        results = self.get(url)
        return results

    def createSubnet(self, payload):
        """
        Description
        -----------
        Creates subnet object in phpIPAM.

        Parameters
        ----------
        payload: dict
            subnet: ip
                A string containing the subnet (w.x.y.z).
            mask: int 
                An integer containing the number of network bits.
                Ex. Let the CIDR network be w.x.y.z/ab. The "mask" value would be represented as "ab".
            sectionId: integer
                An integer representing the phpIPAM identifier for the target section to place the subnet into.
                A string containing the name for the subnet.
            scanAgent: 1
                Include key "scanAgent" with value of "1". Otherwise a random error is generated.
            (optional) location: int
                An integer representing the phpIPAM identifier for the target location to associate the subnet to.
            (optional) masterSubnetId: int
                An integer representing the phpIPAM identifier for the parent subnet/folder.
            (optional) vlanId: int
                An integer representing the phpIPAM identifier for the target VLAN to associate to the subnet.
            (optional) showName: binary integer
                An integer value of either 1 or 0 to control whether or not the subnet is displayed by name.
            (optional) pingSubnet: binary integer
                An integer value of either 1 or 0 to control whether or not the subnet is ping scanned.
            (optional) discoverSubnet: binary integer
                An integer value of either 1 or 0 to control whether or not new hosts are allowed to be discovered within the subnet.
            

        Returns
        -------
        result: int
            HTTP status code of operation.
        """
        url = self.urlBase + "subnets"
        results = self.post(url, payload)
        return results

    def updateSubnet(self, payload):
        """
        Description
        -----------
        Updates subnet object in phpIPAM.

        Parameters
        ----------
        payload: dict
            id: int
                An integer representing the phpIPAM identifier for the subnet.
            sectionId: integer
                An integer representing the phpIPAM identifier for the target section to place the subnet into.
                A string containing the name for the subnet.
            scanAgent: 1
                Include key "scanAgent" with value of "1". Otherwise a random error is generated.
            (optional) location: int
                An integer representing the phpIPAM identifier for the target location to associate the subnet to.
            (optional) masterSubnetId: int
                An integer representing the phpIPAM identifier for the parent subnet/folder.
            (optional) vlanId: int
                An integer representing the phpIPAM identifier for the target VLAN to associate to the subnet.
            (optional) showName: binary integer
                An integer value of either 1 or 0 to control whether or not the subnet is displayed by name.
            (optional) pingSubnet: binary integer
                An integer value of either 1 or 0 to control whether or not the subnet is ping scanned.
            (optional) discoverSubnet: binary integer
                An integer value of either 1 or 0 to control whether or not new hosts are allowed to be discovered within the subnet.

        Returns
        -------
        result: int
            HTTP status code of operation.
        """
        url = self.urlBase + "subnets"
        results = self.patch(url, payload)
        return results

    def getVLANs(self, specific=False):
        """
        Description
        -----------
        Obtains VLAN objects from phpIPAM.

        Parameters
        ----------
        (optional) specific: int
            An integer representing the VLAN object in phpIPAM.

        Returns
        -------
        result: dictionary
            Obtains ALL VLANs within the entirety of phpIPAM.
        """
        url = self.urlBase + 'vlan'
        if specific:
            url += '/' + str(specific)
        results = self.get(url)
        return results

    def getSubnetHosts(self, subnet):
        """
        Description
        -----------
        Obtains address objects from a specified subnet from phpIPAM.

        Parameters
        ----------
        subnet: string
            A CIDR formatted (w.x.y.z/ab) subnet.

        Returns
        -------
        if the subnet exists:
            if the subnet has hosts:
                results: dictionary
                    key:value attributes about the address objects within the specified subnet.
            else:
                results: string
                    A message stating "No addresses found".
        else:
            results: string
                A message stating "No subnets found".
        """
        subnetDict = self.getSubnets(subnet)
        if subnetDict == "No subnets found":
            return subnetDict
        subnetID = subnetDict['id']
        url = self.urlBase + 'subnets/' + subnetID + '/addresses'
        results = self.get(url)
        return results

    def getLocation(self, specific=False):
        """
        Description
        -----------
        Obtains location objects from phpIPAM.

        Parameters
        ----------
        (optional) specific: id
            integer representing the object ID from phpIPAM.

        Returns
        -------
        if specific=False:
            result: dictionary
                Obtains ALL locations within the entirety of phpIPAM.
        else:
            results: dictionary
                Obtains one specific location object and its key:value attributes.
        """
        url = self.urlBase + "tools/locations"
        if specific:
            url += '/' + specific
        results = self.get(url)
        return results['data']

    def addLocation(self, payload):
        """
        Description
        -----------
        Creates location objects in phpIPAM.

        Parameters
        ----------
        payload: dict
            name: string
                A string containing the name of the location object.
            (optional) description: string
                A description for the location object
            (optional) address: string
                A string containing the street address for the location object.
            (optional) longitude: string
                A string containing the longitude coordinate for the location object.
            (optional) latitude: string
                A string containing the latitude coordinate for the location object.

        Returns
        -------
        result: int
            HTTP status code of operation.
        """
        url = self.urlBase + "tools/locations"
        results = self.post(url, payload)
        return results

    def updateLocation(self, payload):
        """
        Description
        -----------
        Updates location objects in phpIPAM.

        Parameters
        ----------
        payload: dictionary
            id: int
                An integer representing the ID for the location object.
            (optional) name: string
                A string containing the name for the location object
            (optional) description: string
                A string containing the description for the location object
            (optional) address: string
                A string containing the street address for the location object.
            (optional) longitude: string
                A string containing the longitude coordinate for the location object.
            (optional) latitude: string
                A string containing the latitude coordinate for the location object.

        Returns
        -------
        result: int
            HTTP status code of operation.
        """
        url = self.urlBase + "tools/locations/" + id
        results = self.put(url, payload)
        return results
    
    def deleteLocation(self, id):
        """
        Description
        -----------
        Deletes location object in phpIPAM.

        Parameters
        ----------
        id: int
            An integer representing the ID for the location object.

        Returns
        -------
        result: int
            HTTP status code of operation.
        """
        url = self.urlBase + "tools/locations/" + id
        results = self.delete(url)
        return results

    def getDevices(self, specific=False):
        """
        Description
        -----------
        Obtains device objects from phpIPAM.

        Parameters
        ----------
        (optional) specific: int
            integer representing the object ID from phpIPAM.

        Returns
        -------
        if specific=False:
            result: dictionary
                Obtains ALL device within the entirety of phpIPAM.
        else:
            results: dictionary
                Obtains one specific device object and its key:value attributes.
        """
        url = self.urlBase + 'devices'
        if specific:
            url += '/' + str(specific)
        results = self.get(url)
        return results

    def addDevice(self, payload):
        """
        Description
        -----------
        Creates device objects in phpIPAM.

        Parameters
        ----------
        payload: dictionary
            hostname: string
                A string containing the name of the device object.
            (optional) description: string
                A description for the device object
            (optional) ip: string
                A string containing the IPv4 address for the object.
            (optional) type: int
                An integer value representing the IPAM Device Type object to link to the device.
            (optional) sections: int
                An integer value representing the IPAM section object to link to the device. 
            (optional) location: int
                An integer value representing the IPAM location object to link to the device.

        Returns
        -------
        result: int
            HTTP status code of operation.
        """
        url = self.urlBase + "devices"
        results = self.post(url, payload)
        return results


    def updateDevice(self, payload):
        """
        Description
        -----------
        Updates device objects in phpIPAM.

        Parameters
        ----------
        payload: dictionary
            id: int
                An integer value representing the device object.
            (optional) hostname: string
                A string containing the name of the device object.
            (optional) description: string
                A description for the device object
            (optional) ip: string
                A string containing the IPv4 address for the object.
            (optional) type: int
                An integer value representing the IPAM Device Type object to link to the device.
            (optional) sections: int
                An integer value representing the IPAM section object to link to the device. 
            (optional) location: int
                An integer value representing the IPAM location object to link to the device.

        Returns
        -------
        result: int
            HTTP status code of operation.
        """
        url = self.urlBase + "devices"
        results = self.patch(url, payload)
        return results

    def deleteDevice(self, id):
        """
        Description
        -----------
        Deletes device object in phpIPAM.

        Parameters
        ----------
        id: int
            An integer representing the ID for the device object.

        Returns
        -------
        result: int
            HTTP status code of operation.
        """
        url = self.urlBase + "devices/" + str(id)
        results = self.delete(url)
        return results

    def getDeviceTypes(self, specific=False, devices=False):
        """
        Description
        -----------
        Obtains device type objects from phpIPAM.

        Parameters
        ----------
        (optional) specific: int
            integer representing the object ID from phpIPAM.

        Returns
        -------
        if specific=False:
            result: dictionary
                Obtains ALL device type objects within the entirety of phpIPAM.
        else:
            results: dictionary
                Obtains one specific device type object and its key:value attributes.
        """
        url = self.urlBase + 'tools/device_types'
        if specific:
            url += '/' + str(specific)
            if devices:
                url += '/devices'
        results = self.get(url)
        return results

    def getSections(self, specific=False, devices=False):
        """
        Description
        -----------
        Obtains section objects from phpIPAM.

        Parameters
        ----------
        (optional) specific: int
            integer representing the object ID from phpIPAM

        Returns
        -------
        if specific = False:
            result: dictionary
                Obtains ALL section type objects within the entirety of phpIPAM.
        else:
            results: dictionary
                Obtains one specific device type object and its key:value attributes.
        """
        url = self.urlBase + 'sections'
        if specific:
            url += '/' + str(specific)
            if devices:
                url += '/devices'
        results = self.get(url)
        return results

    def searchDevice(self, payload):
        """
        Description
        -----------
        Searches IPAM device database for hostname search string.

        Parameters
        ----------
        payload: string
            A string value containing the hostname to index for.
            
        Returns
        -------
        result: dictionary
            if a device is found: 
                result['success'] = True
                result['data'][0] = {
                    deviceAttribute: attributeValue,
                    deviceAttribute2: attrbute2Value
                }
            else:
                result['success'] = False        
        """
        url = self.urlBase + 'devices/search/' + payload
        results = self.get(url)
        return results

    def removeAllAddressesFromSubnet(self, subnetId):
        """
        Description
        -----------
        Removes all address objects from subnet.

        Parameters
        ----------
        subnetId: int
            An integer representing the phpIPAM id for the target subnet.
            
        Returns
        -------
        result: int
            if result == 200:
                Subnet truncated.
            else:
                HTTP error code, investigate as appropriate.
        """
        url = self.urlBase + 'subnets/' + str(subnetId) + "/truncate"
        results = self.delete(url)
        return results

    def createAddress(self, payload):
        """
        Description
        -----------
        Creates an address object.

        Parameters
        ----------
        subnetId: int
            An integer representing the phpIPAM id for the subnet in which the address will live.
        ip: string
            A string containing a 32-bit IP address (w.x.y.z).
        is_gateway: binary integer
            An integer value of either 1 or 0 to control whether or not the address should be considered the subnet's gateway.
        description: string
            A string value containing a description for the IP address.
        hostname: string
            A string value containing a hostname to associate to the IP address object.
        mac: string
            A string value containing the MAC address to associate to the address object.
        owner: string
            A string value containing an "owner" for the IP address object.
        tag: int
            An integer value of 1-4 (assuming no custom tags) to assign one of the following tags to the IP address object:
                1: Offline
                2: Used
                3: Reserved
                4: DHCP
        deviceId: int
            An integer value representing the phpIPAM id for the device in which the address belongs to.
        
        See https://phpipam.net/api/api_documentation/ for more values.
            
        Returns
        -------
        result: int
            if result == 201:
                Address created.
            else:
                HTTP error code, investigate as appropriate.
        """
        url = self.urlBase + 'addresses'
        results = self.post(url, payload)
        return results