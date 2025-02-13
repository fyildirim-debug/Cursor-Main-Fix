import os
import re
import random
import shutil
import pathlib
import platform
from uuid import uuid4
import json
import sys



def print_status(status, data=None):
    output = {
        "status": status
    }

    if data:
        output["data"] = data
    print(json.dumps(output))
    sys.stdout.flush()

def print_error(error, data=None):
    if isinstance(error, Exception):
         error = str(error).replace('\n', ' ').strip()
    output = {
        "error": error
    }
    if data:
        output["data"] = data
    sys.stderr.write(json.dumps(output) + "\n")

SYSTEM = platform.system()
if SYSTEM not in ("Windows", "Linux", "Darwin"):
    print_error(f"Unsupported OS: {SYSTEM}")
    exit()
if SYSTEM == "Windows":
    # ANSI Support for OLD Windows
    os.system("color")


def uuid():
    return str(uuid4())


def path(path: str | pathlib.Path):
    return pathlib.Path(path).resolve()


def curbasepath():
    if SYSTEM == "Windows":
        localappdata = os.getenv("LOCALAPPDATA")
        assert localappdata, "Panicked: LOCALAPPDATA not exist"
        return path(localappdata) / "Programs" / "cursor" / "resources" / "app"
    elif SYSTEM == "Darwin":
        return path("/Applications/Cursor.app/Contents/Resources/app")
    elif SYSTEM == "Linux":
        bases = [
            path("/opt/Cursor/resources/app"),
            path("/usr/share/cursor/resources/app"),
        ]
        for base in bases:
            if base.exists():
                return base
        print(f"[ERR] Cursor base path not found, please specify")
        exit()
    else:
        assert None


def jspath(p: str):
    if not p:
        jspath = curbasepath() / "out" / "main.js"
        if not jspath.exists():
            print_error(f"main.js not found in default path '{jspath}'")
            exit()
        print_status("Success", {"path": str(jspath)})
    else:
        jspath = path(p)
        if not jspath.exists():
            print_error(f"File '{jspath}' not found")
            exit()
    return jspath


def randomuuid(randomuuid: str):
    if not randomuuid:
        randomuuid = uuid()
        print_status("Generated UUID", {"uuid": randomuuid})
    return randomuuid


def macaddr(macaddr: str):
    if not macaddr:
        while not macaddr or macaddr in (
            "00:00:00:00:00:00",
            "ff:ff:ff:ff:ff:ff",
            "ac:de:48:00:11:22",
        ):
            macaddr = ":".join([f"{random.randint(0, 255):02X}" for _ in range(6)])
        print_status("Generated MAC address", {"mac": macaddr})
    return macaddr


def load(path: pathlib.Path):
    with open(path, "rb") as f:
        return f.read()


def save(path: pathlib.Path, data: bytes):
    print_status("Saving file", {"path": str(path)})
    try:
        with open(path, "wb") as f:
            f.write(data)
            print_status("File saved successfully")
            print_status("OK")
    except PermissionError:
        print_error(
            f"Permission denied",
            {"message": f"The file '{path}' is in use, please close it and try again"}
        )
        exit()


def backup(path: pathlib.Path):
    print_status("Creating backup", {"file": path.name})
    bakfile = path.with_name(path.name + ".bak")
    if not os.path.exists(bakfile):
        shutil.copy2(path, bakfile)
        print_status("Backup created", {"backup_file": bakfile.name})
    else:
        print_status("Backup exists", {"backup_file": bakfile.name})


def replace(
    data: bytes, pattern: str | bytes, replace: str | bytes, probe: str | bytes
) -> bytes:
    if isinstance(pattern, str):
        pattern = pattern.encode()
    if isinstance(replace, str):
        replace = replace.encode()
    if isinstance(probe, str):
        probe = probe.encode()
    assert isinstance(pattern, bytes)
    assert isinstance(replace, bytes)
    assert isinstance(probe, bytes)
    print_status("Replacing pattern", {
        "from": pattern.decode(),
        "to": replace.decode()
    })

    regex = re.compile(pattern, re.DOTALL)
    count = len(list(regex.finditer(data)))
    patched_regex = re.compile(probe, re.DOTALL)
    patched_count = len(list(patched_regex.finditer(data)))

    if count == 0:
        if patched_count > 0:
            print_status("Found already patched patterns", {"count": patched_count})
        else:
            print_status("Warning", {
                "message": f"Pattern <{pattern}> not found, SKIPPED!"
            })
            return data

    data, replaced1_count = patched_regex.subn(replace, data)
    data, replaced2_count = regex.subn(replace, data)
    replaced_count = replaced1_count + replaced2_count
    if replaced_count != count + patched_count:
        print_status("Warning", {
            "message": f"Patched {replaced_count}/{count}, failed {count - replaced_count}"
        })
    else:
        print_status("Patching complete", {
            "patched_count": replaced_count
        })
    return data


js = jspath("")
data = load(js)

machineid = randomuuid("")

# async function machineId(returnRaw) {
#     let machineid = processOutput(execSync(commands[PLATFORM], { timeout: 5e3 }).toString()),
#         hash;
#     try {
#         hash = (await import("crypto")).createHash("sha256").update(machineid, "utf8").digest("hex");
#     } catch {
#         hash = uuid();
#     }
#     return returnRaw ? machineid : hash;
# }
data = replace(
    data,
    r"=.{0,50}timeout.{0,10}5e3.*?,",
    f'=/*csp1*/"{machineid}"/*1csp*/,',
    r"=/\*csp1\*/.*?/\*1csp\*/,",
)

mac = macaddr("")
# function getMacAddress() {
#     const interfaces = networkInterfaces();
#     for (const name in interfaces) {
#         const details = interfaces[name];
#         if (details) {
#             for (const { mac: m } of details) if (isValidMac(m)) return m;
#         }
#     }
#     throw new Error("Unable to retrieve mac address (unexpected format)");
# }
data = replace(
    data,
    r"(function .{0,50}\{).{0,300}Unable to retrieve mac address.*?(\})",
    f'\\1return/*csp2*/"{mac}"/*2csp*/;\\2',
    r"()return/\*csp2\*/.*?/\*2csp\*/;()",
)

sqm = ""
# async function sqmId(errorBind) {
#     if (isWindows) {
#         const reg = await import("@vscode/windows-registry");
#         try {  // REGPATH = "Software\\Microsoft\\SQMClient"
#             return (reg.GetStringRegKey("HKEY_LOCAL_MACHINE", REGPATH, "MachineId") || "");
#         } catch (e) {
#             return errorBind(e), "";
#         }
#     }
#     return "";
# }
data = replace(
    data,
    r'return.{0,50}\.GetStringRegKey.*?HKEY_LOCAL_MACHINE.*?MachineId.*?\|\|.*?""',
    f'return/*csp3*/"{sqm}"/*3csp*/',
    r"return/\*csp3\*/.*?/\*3csp\*/",
)

devid = randomuuid("")
# async function devDeviceId(errorBind) {
#     try {
#         return await (await import("@vscode/deviceid")).getDeviceId();
#     } catch (e) {
#         return errorBind(e), uuid();
#     }
# }
data = replace(
    data,
    r"return.{0,50}vscode\/deviceid.*?getDeviceId\(\)",
    f'return/*csp4*/"{devid}"/*4csp*/',
    r"return/\*csp4\*/.*?/\*4csp\*/",
)

# Backup and save
backup(js)
save(js, data)
