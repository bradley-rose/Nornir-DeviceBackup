from cryptography.fernet import Fernet

def decryptCredentials(devices):
    with open("Hosts Encryption Key.txt", "rb") as file:
        key = file.read()
    cipher = Fernet(key)
    for device in devices.inventory.hosts.values():
        device.username = cipher.decrypt(device.username.encode('UTF-8'))
        device.password = cipher.decrypt(device.password.encode('UTF-8'))
        device.username = device.username.decode('UTF-8')
        device.password = device.password.decode('UTF-8')