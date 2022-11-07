from cryptography.fernet import Fernet

def decryptCredentials(devices):
    try:
        with open("Functions/Hosts Encryption Key.txt", "rb") as file:
            key = file.read()
    except FileNotFoundError:
        with open("Hosts Encryption Key.txt", "rb") as file:
            key = file.read()
    cipher = Fernet(key)
    for device in devices.inventory.hosts.values():
        try:
            device.username = cipher.decrypt(device.username.encode('UTF-8')).decode('UTF-8')
            device.password = cipher.decrypt(device.password.encode('UTF-8')).decode('UTF-8')
        except:
            continue

def decryptAPIuser(username, password):
    try:
        with open("Functions/Hosts Encryption Key.txt", "rb") as file:
            key = file.read()
    except FileNotFoundError:
        with open("Hosts Encryption Key.txt", "rb") as file:
            key = file.read()
    cipher = Fernet(key)
    return cipher.decrypt(username.encode('UTF-8')).decode('UTF-8'), cipher.decrypt(password.encode('UTF-8')).decode('UTF-8')