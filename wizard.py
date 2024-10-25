import platform,os,json,stat,sys
from getpass import getpass, getuser
import base64

#for retrieving webDrivers
import requests
import zipfile
import tarfile
import wget

settings = {}

def validateSystem():
    if (platform.system() != "Windows") and (platform.system() != "Linux") and (platform.system() != "Darwin"):
        print("Sorry, this script currently only supports Windows, Linux and Darwin Kernels")
        exit()
    if (platform.architecture()[0] != "64bit") and (platform.architecture()[0] != "32bit") and (sys.maxsize < (2**31 - 1)):
        print("Sorry, this script currently only supports AMD64, x86, ARM7+ and Mac 32/64 bit architectures")
        exit()

def settingsQuestions():
    #User input for browser selection and version
    print("Running first time set-up..")
    if platform.architecture()[1] == "ELF": # raspi support added
        userBrowser = str(input("Firefox is required to use this script on ARM, is Firefox installed on this device? (y/n)"))
        if (len(userBrowser) > 0):
            if (userBrowser.lower())[0] == 'y':
                settings['browser'] = 'firefox'
                settings['version'] = "v0.23.0"
            elif (userBrowser.lower())[0] == 'n':
                print("Install Firefox by copying and pasting following command into your command line terminal:")
                print("sudo apt install firefox-esr")
                print("After installation run this script again.\n This script will now exit")
                exit()
            else:
                print("Sorry, the the script was expecting a y/n, but you submitted: {0}\nExiting...".format(userBrowser))
                exit()
        else:
            print("Sorry, the the script was expecting a y/n, but you submitted: {0}\nExiting...".format(userBrowser))
            exit()
    else:
        userBrowser = str(input("Are you using Firefox or Chrome? (Firefox gives a better automated headless experience) (accepts f or c): "))
        if (len(userBrowser) > 0):
            if (userBrowser.lower())[0] == 'c':
                settings['browser'] = 'chrome'
                userBrowserVersion = str(input("What is your installed Chrome's full version number? eg. 83.0.4103.61 (can be found here: chrome://settings/help ): "))
                if len(userBrowserVersion.split('.')) == 4:
                    settings['version'] = userBrowserVersion
                else:
                    print("Sorry, the the script was expecting your installed Chrome's FULL version number, but you submitted: {0}\nExiting...".format(userBrowserVersion))
                    exit()
            elif (userBrowser.lower())[0] == 'f':
                settings['browser'] = 'firefox'
                settings['version'] = "v0.26.0"
                #settings['version'] = int(input("What is your installed Firefox's major version number? eg. 76 (can be found under Menu > Help > About Firefox ): "))
            else:
                print("Sorry, the the script was expecting an f/F/firefox/Firefox or c/C/chrome/Chrome, but you submitted: {0}\nExiting...".format(userBrowser))
                exit()
        else:
            print("Sorry, the the script was expecting an f/F/firefox/Firefox or c/C/chrome/Chrome, but you submitted: {0}\nExiting...".format(userBrowser))
            exit()

    userEmail = str(input("Your MindSphere username (email): "))
    #if ((len(userEmail.split('@')) != 2) and (len((userEmail.split('@')).split('.')) != 2)):    #validate email address
    if ((len(userEmail.split('@')) != 2)):    #validate email address
        print("Sorry, the the script was expecting a valid email address, but you submitted: {0}\nExiting...".format(userEmail))
        exit()
    elif (len((userEmail.split('@'))[1].split('.')) < 2):
        print("Sorry, the the script was expecting a valid email address, but you submitted: {0}\nExiting...".format(userEmail))
        exit()
    settings['email'] = userEmail

    userPassword = getpass('Your MindSphere Password:')
    settings['password'] = (base64.b64encode(userPassword.encode('ascii'))).decode('utf-8')


    userURL = str(input("MindSphere URL to autologin and keep refreshed: "))
    if not (userURL.startswith('https://')):
        print("Sorry, the the script was expecting a valid url starting with 'https://', but you submitted: {0}\nExiting...".format(userURL))
        exit()
    settings['url'] = userURL

    if (platform.system() == "Windows"):
        userResponse = str(input("Create batch file and add to user's startup folder for Windows start-on-boot functionality? (Check README for further information) (y/n): "))
        if (userResponse.lower().startswith('y')):
            createBatchFile()
    return settings

def writeSettings(settings):
    with open("config.json", "w") as outfile:
        json.dump(settings, outfile, indent=4, sort_keys=True)

def installBrowserEngine(settings):
    OS = 'arm' if (platform.architecture()[1] == "ELF") else 'win' if (platform.system() == "Windows") else 'macos' if (platform.system() == "Darwin") else 'linux'
    extension = 'zip' if (platform.system() == "Windows") else 'tar.gz'
    arch = '7hf' if (platform.architecture()[1] == "ELF") else '' if (platform.system() == "Darwin") else platform.architecture()[0][0:2]
    if settings['browser'] == "firefox":
        #check if already exists here
        #check if raspi - use most recent compatible build - static URL unless you want to build from source lol, just kinda shoved this in so fingers crossed.
        firefox_driver_url = 'https://github.com/mozilla/geckodriver/releases/download/{0}/geckodriver-{0}-{1}{2}.{3}'.format(settings['version'],OS,arch,extension)
        print("Attempting to download geckodriver version {0} from {1}".format(settings['version'],firefox_driver_url))
        wget.download(firefox_driver_url,'./')
        if (extension == 'zip'):
            with zipfile.ZipFile('./geckodriver-{0}-{1}{2}.{3}'.format(settings['version'],OS,arch,extension), 'r') as zip_ref:
                zip_ref.extractall('./')
        else:
            tar = tarfile.open('./geckodriver-{0}-{1}{2}.{3}'.format(settings['version'],OS,arch,extension), 'r:gz')
            tar.extractall(path='./')
            tar.close()
        os.remove('./geckodriver-{0}-{1}{2}.{3}'.format(settings['version'],OS,arch,extension))
    else:   #chrome
        #check if already exists here
        chromeSystem = 'win32' if (OS == 'win') else'mac64' if (OS == 'macos') else 'linux64'
        chromeSubVersion = "{0}.{1}.{2}".format((settings['version'].split('.')[0]),(settings['version'].split('.')[1]),(settings['version'].split('.')[2]))
        latestCompatibleChromeURL = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{0}'.format(chromeSubVersion)
        latestCompatibleChromeVersion = ((requests.get(latestCompatibleChromeURL)).content).decode("utf-8") 
        chromeDriverDownloadURL = 'https://chromedriver.storage.googleapis.com/{0}/chromedriver_{1}.zip'.format(latestCompatibleChromeVersion,chromeSystem)
        print("Attempting to download chromedriver version {0} from {1}".format(latestCompatibleChromeVersion,chromeDriverDownloadURL))
        wget.download(chromeDriverDownloadURL,'./')
        with zipfile.ZipFile('./chromedriver_{0}.zip'.format(chromeSystem), 'r') as zip_ref:
            zip_ref.extractall('./')
        if (platform.system() == 'Linux'):  #If linux + Chrome, make the binary executable (doesn't come with +x)
            st = os.stat('./chromedriver')
            os.chmod('./chromedriver', st.st_mode | stat.S_IEXEC)
        os.remove('./chromedriver_{0}.zip'.format(chromeSystem))
    #got to here, wizard complete
    print('\nweb engine succesfully installed')
    settings['wizardRan'] = True
    writeSettings(settings)

def createBatchFile():
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    startupFolderPath = r'C:\Users\{0}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'.format(getuser())
    batName = "MindSphereAutologin.bat"
    try:
        print("Attempting to save {0} in {1}".format(batName,startupFolderPath))
        with open(startupFolderPath + '\\' + batName, "w+") as bat_file:
            bat_file.write('cd {0}\n"py" "autologin.py"\npause'.format(scriptPath))
            print("Successfully wrote {0} to {1} !\nThis autologin script should now run on windows startup.\nPlease note that if you move this script into a different directory, the run-on-boot functionality will break and you will have to run the wizard again".format(batName,startupFolderPath))
    except:
        print("Failed to write {0} to {1}\nPlease try running this script again as admin".format(batName,startupFolderPath))
        exit()