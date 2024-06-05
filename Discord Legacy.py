import sys, os, tempfile, requests, subprocess, shutil
version = "1.4"
localrun = False
origdir = os.getcwd()

def clear():
    print("\033c", end='')

discordpackages = {
    "macOS 10.14" :  "0.0.296",
    "macOS 10.13" :  "0.0.296",
    "macOS 10.12" :  "0.0.273",
    "OS X 10.11"  :  "0.0.273",
    "OS X 10.10"  :  "0.0.262",
    "OS X 10.9"   :  "0.0.255",
}

def preflight():
    os.chdir(origdir)
    global localrun
    try:
        output = subprocess.check_output([f"{sys._MEIPASS}/files/asar","--version"])
    except:
        print("Running from source code.\nYou can download a release from https://github.com/Jazzzny/Discord-Legacy/releases/")
        localrun = True
        try:
            output = subprocess.check_output(["node","--version"])
            nodever = output.decode("utf-8")[1:-1]
            output1 = subprocess.check_output(["npm","--version"])
            npmver = output1.decode("utf-8")[:-1]
            if int(nodever.split(".")[0]) > 9:
                print(f"✅ Node.js {nodever} installed\n✅ Node Package Manager {npmver} installed")
            else:
                print("❌ Node.js is too old! Please install Node.js 10+.")
                sys.exit()
        except FileNotFoundError:
            print("❌ Node.js is not installed! Please install Node.js 10+.")
            sys.exit()
        try:
            output2 = subprocess.check_output(["npx","asar","--version"])
            asarver = output2.decode("utf-8")[1:-1]
            print(f"✅ @electron/asar {asarver} installed")
        except subprocess.CalledProcessError:
            print("❌ Asar library is not installed! Please install it by running 'npm i @electron/asar'.")
            sys.exit()
        print("====================================================")

def mktemp():
    global temp_dir
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    print(f"Established temporary directory at \n{temp_dir}")

def copyfiles():
    print("Mounting disk image")
    subprocess.call(["/usr/bin/hdiutil","attach","./Discord.dmg","-nobrowse","-noverify","-quiet"])
    print("Copying files")
    try:
        shutil.copytree("/Volumes/Discord/Discord.app/","./Discord/Discord.app/",symlinks=True) #will try to copy the entire applications folder if set to false
    except:
        print("Could not mount disk image/copy files. Please restart your machine.")
        sys.exit()
    print("Ejecting disk image")
    subprocess.call(["/usr/bin/hdiutil","eject","/Volumes/Discord"])

def downloaddiscord(build):
    print("====================================================")
    url = f"https://dl.discordapp.net/apps/osx/{build}/Discord.dmg"
    print(f"Downloading Discord {build} from \n{url}\nThis may take a while.")
    response = requests.get(url, stream=True)
    with open("Discord.dmg", 'wb') as f:
        total_size = int(response.headers.get('content-length', 0))
        progress = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                progress += len(chunk)
                percent_done = int(progress / total_size * 100)
                print(f"Download progress: {percent_done}%", end='\r')

def downloadlatestdiscord():
    print("====================================================")
    url = f"https://discord.com/api/download?platform=osx"
    print(f"Downloading Discord (Latest) from \n{url}\nThis may take a while.")
    response = requests.get(url, stream=True)
    with open("Discord.dmg", 'wb') as f:
        total_size = int(response.headers.get('content-length', 0))
        progress = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                progress += len(chunk)
                percent_done = int(progress / total_size * 100)
                print(f"Download progress: {percent_done}%", end='\r')

def downloadopenasar(ver):
    print(f"Downloading OpenAsar-Legacy for {ver}")
    catalog = requests.get("https://api.github.com/repos/jazzzny/openasar-legacy/releases")
    catalog = catalog.json()
    compatiblebuilds = {}

    for release in catalog:
        if release["name"] >= ver:
            for asset in release["assets"]:
                if asset["name"].endswith(".asar"):
                    compatiblebuilds[release["name"]]=asset["browser_download_url"]
    try:
        if list(sorted(compatiblebuilds.items()))[0][0] != ver:
            print(f"WARNING: No matching OpenAsar-Legacy build found! Will use closest match - {list(sorted(compatiblebuilds.items()))[0][0]}")
    except:
        print("WARNING: No matching OpenAsar-Legacy build found! Will use latest.")
    print(f"Downloading {list(sorted(compatiblebuilds.items()))[0][1]}")
    response = requests.get(list(sorted(compatiblebuilds.items()))[0][1], stream=True)
    with open("app.asar", 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print("Moving app.asar")
    shutil.move("app.asar","./Discord/Discord.app/Contents/Resources/app.asar")

def upgradeelectron(ver):
    print("Upgrading Electron")
    shutil.rmtree("./Discord/Discord.app/Contents/Frameworks/")
    os.mkdir("./Discord/Discord.app/Contents/Frameworks/")
    print("Downloading Electron 21.0.0-nightly.20220531")
    response = requests.get("https://github.com/electron/nightlies/releases/download/v21.0.0-nightly.20220531/electron-v21.0.0-nightly.20220531-darwin-x64.zip", stream=True)
    with open("electron.zip", 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print("Extracting Electron")
    subprocess.call(["/usr/bin/unzip","electron.zip","-d","./Electron/"])

    # Move all contents of Electron.app/Contents/Frameworks to Discord.app/Contents/Frameworks
    print("Moving Electron")
    for file in os.listdir("./Electron/Electron.app/Contents/Frameworks/"):
        shutil.move(f"./Electron/Electron.app/Contents/Frameworks/{file}","./Discord/Discord.app/Contents/Frameworks/")

    # Delete Electron
    shutil.rmtree("./Electron/")

def adhocsign():
    print("Adhoc Signing Discord")
    subprocess.call(["/usr/bin/codesign","--force","--deep","-s", "-", "./Discord/Discord.app"])

def extractasar():
    global localrun
    print("Extracting app.asar")
    if localrun == True:
        subprocess.call(["npx","asar","extract","./Discord/Discord.app/Contents/Resources/app.asar","./app/"])
    else:
        subprocess.call([f"{sys._MEIPASS}/files/asar","extract","./Discord/Discord.app/Contents/Resources/app.asar","./app/"])

def packasar():
    global localrun
    print("Packing app.asar")
    if localrun == True:
        subprocess.call(["npx","asar","pack","./app/","./Discord/Discord.app/Contents/Resources/app.asar"])
    else:
        subprocess.call([f"{sys._MEIPASS}/files/asar","pack","./app/","./Discord/Discord.app/Contents/Resources/app.asar"])

    print("Deleting extracted app.asar folder")
    shutil.rmtree("./app/")

def patchupdater():
    print("Patching Updater")
    with open('./app/common/moduleUpdater.js','r') as file:
        filedata = file.read()
        filedata = filedata.replace("settings.get(SKIP_HOST_UPDATE)","true")
    with open('./app/common/moduleUpdater.js','w') as file:
        file.write(filedata)

def fixminver(): #0.0.255 needs to have it's minimum version adjusted to support 10.9
    print("Patching LSMinimumSystemVersion")
    with open('./Discord/Discord.app/Contents/Info.plist','r') as file:
        filedata = file.read()
        filedata = filedata.replace("10.10","10.9")
    with open('./Discord/Discord.app/Contents/Info.plist','w') as file:
        file.write(filedata)
    subprocess.call(["xattr","-dr","com.apple.quarantine","./Discord/Discord.app"])

def movetodownloads():
    print("Moving patched disk image to Downloads folder")
    shutil.move("./Discord.dmg",os.path.expanduser('~/Downloads')+"/DiscordPatched.dmg")

def makerwdmg():
    print("Creating R/W disk image")
    subprocess.call(["/usr/bin/hdiutil","convert","-format","UDRW","-o","./Discord_RW.dmg","./Discord.dmg","-quiet"])
    print("Deleting original disk image")
    os.remove("Discord.dmg")
    print("Mounting R/W disk image")
    subprocess.call(["/usr/bin/hdiutil","attach","./Discord_RW.dmg","-nobrowse","-noverify","-quiet"])
    print("Moving patched application")
    shutil.rmtree("/Volumes/Discord/Discord.app")
    shutil.move("./Discord/Discord.app","/Volumes/Discord/Discord.app")
    print("Ejecting and finalizing disk image")
    subprocess.call(["/usr/bin/hdiutil","eject","/Volumes/Discord"])
    subprocess.call(["/usr/bin/hdiutil","convert","-format","UDZO","-o","./Discord.dmg","./Discord_RW.dmg","-quiet"])

def cleartemp():
    shutil.rmtree("./Discord")
    os.remove("Discord_RW.dmg")

def preparepackage(version):
    clear()
    mktemp()
    selectedclient = "0.0.999"
    if version != 1 and version != 6: #1 is latest, 6 is custom
        selectedmacOSBuild = list(discordpackages.keys())[version-2]
        selectedclient = discordpackages[selectedmacOSBuild]

    print("====================================================")

    if version == 1:
        print("Preparing to download Discord (Latest) for 10.13+")
        downloadlatestdiscord()
    elif version == 6:
        selectedclient = input("\nPlease enter the build you wish to download: ")
        downloaddiscord(selectedclient)
        print(f"Preparing to download Discord")
    else:
        print(f"Preparing to download Discord {selectedclient} for {selectedmacOSBuild}")
        downloaddiscord(selectedclient)
    print("====================================================")
    clear()
    print("====================================================")
    print(f"Patching Discord")
    print("====================================================")
    copyfiles()
    if selectedclient > "0.0.255" and selectedclient != "0.0.999":
        openasarselection = input("\aWould you like to install OpenAsar-Legacy? (y/n): ").lower()
    else:
        openasarselection = ""
    if openasarselection == "y":
        downloadopenasar(selectedclient)
    else:
        extractasar()
        patchupdater()
        packasar()
    if selectedclient == "0.0.255":
        fixminver()

    if selectedclient == "0.0.273":
        upgradeelectron(selectedclient)
        adhocsign()

    makerwdmg()
    movetodownloads()
    cleartemp()
    clear()
    print("====================================================")
    print(f"Patching Complete")
    print("====================================================")
    input("The patched Discord Client has been placed in your Downloads folder.\nPress enter to continue.")

def mainmenu():
    clear()
    print(
f"""====================================================
Discord Legacy Patcher {version}
====================================================
Discord Legacy Patcher will download the chosen
build, apply the required patches, and create a
patched disk image.
====================================================
"""
,end="")
    preflight()
    print("1. Latest Client (Disables Discord Updates, macOS 10.15+)")
    for ind, (ver,build) in enumerate(discordpackages.items()):
        print(f"{ind+2}. {ver} (Client {build})")
    print("7. Other Client")
    print("8. Exit")
    try:
        choice = int(input("Choose an Option: "))
    except:
        input("Invalid option! Press enter to continue")
        return
    if choice == 8:
        sys.exit()
    else:
        preparepackage(choice)

while True:
    mainmenu()
