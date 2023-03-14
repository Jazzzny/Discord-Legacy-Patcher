import sys, os, tempfile, requests, subprocess, shutil
version = "1.0"
def clear():
    print("\033c", end='')

discordpackages = {
    1:["macOS 10.12","0.0.273"],
    2:["OS X 10.11","0.0.273"],
    3:["OS X 10.10","0.0.262"],
    4:["OS X 10.9","0.0.255"]
}

def preflight():
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
        shutil.copytree("/Volumes/Discord/","./Discord/",symlinks=True) #will try to copy the entire applications folder if set to false
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
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def extractasar():
    print("Extracting app.asar")
    subprocess.call(["npx","asar","extract","./Discord/Discord.app/Contents/Resources/app.asar","./app/"])

def packasar():
    print("Packing app.asar")
    subprocess.call(["npx","asar","pack","./app/","./Discord/Discord.app/Contents/Resources/app.asar"])
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
    print("====================================================")
    if version != 5:
        print(f"Preparing to download Discord {discordpackages[version][1]} for {discordpackages[version][0]}")
    else:
        print(f"Preparing to download Discord")
    print("====================================================")
    
    mktemp()
    if version != 5:
        downloaddiscord(discordpackages[version][1])
    else:
        downloaddiscord(input("Please enter the build you wish to download: "))
    clear()
    print("====================================================")
    print(f"Patching Discord")
    print("====================================================")
    copyfiles()
    extractasar()
    patchupdater()
    packasar()
    if version == 4:
        fixminver()
    makerwdmg()
    movetodownloads()
    cleartemp()
    clear()
    print("====================================================")
    print(f"Patching Complete")
    print("====================================================")
    input("The patched Discord Client has been placed in your Downloads folder.\nPress enter to continue.")
    #subprocess.call(["open",os.path.expanduser('~/Downloads')+"/DiscordPatched/"])
    
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
    for i,v in discordpackages.items():
        print(f"{i}. {v[0]} (Client {v[1]})")
    print("5. Other")
    print("6. Exit")
    choice = int(input("Choose an Option: "))
    if choice == 6:
        sys.exit()
    else:
        preparepackage(choice)
    
while True:
    mainmenu()