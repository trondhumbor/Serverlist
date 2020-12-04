import multiprocessing
import os
import socket
import struct
from datetime import datetime
from ipaddress import ip_address

from Serverlist import scheduler, cache

def reloadServers():
    cache.set("servers", getServerInfo(getServers()))
    cache.set("timestamp", datetime.utcnow())

def getServers():
    app = scheduler.app
    with app.app_context():
        servers = []
        rawResponse = sendMsg(app.config["MASTER_SERVER"], app.config["MASTER_QUERY"], expectEot=True)
        for server in rawResponse.split(b"\\")[1:-1]:
            if len(server) != 6:
                continue
            servers.append((ip_address(server[0:4]).exploded, struct.unpack(">H", server[4:6])[0]))
        return servers

def getServerInfo(servers):
    with multiprocessing.Pool() as pool:
        app = scheduler.app
        with app.app_context():
            serverResponses = pool.starmap(getSingleServer, [(s, app.config["SERVER_INFO"]) for s in servers])
            return [i for i in serverResponses if i is not None]

def getSingleServer(server, query):
    try:
        challenge = os.urandom(4).hex()
        rawResponse = sendMsg(server, query.format(challenge=challenge)).split(b"\\")[1:]
        dct = {k.decode("utf-8"): v.decode("utf-8") for k, v in zip(rawResponse[0::2], rawResponse[1::2])}
        dct["ip"], dct["port"] = server
        if not "challenge" in dct or challenge != dct["challenge"]:
            return None
        return dct
    except socket.timeout:
        return None

def sendMsg(address, message, expectEot=False):
    queryString = b"\xFF\xFF\xFF\xFF" + message.encode("utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    sock.connect(address)
    sock.send(queryString)
    response = sock.recv(8192)
    while expectEot and b"EOT" not in response and b"EOF" not in response:
        response += sock.recv(8192)
    return response
