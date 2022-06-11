import logging
import os
from legendary.downloader.mp.manager import DLManager
from legendary.models.manifest import Manifest
from legendary.models.downloading import FileTask, TaskFlags
from UE4Parse.Provider.DefaultFileProvider import DefaultFileProvider
from UE4Parse.Assets.Objects.FGuid import FGuid
from UE4Parse.Encryption import FAESKey
import requests

from Ini import IniOpen

DOWNLOAD_LOCATION = "./downloads"
COSMETIC_ID = "BID_028_SpaceBlack"

FORTNITE_LOCATION = "D:\Games\Fortnite\Versions\Latest\Fortnite"

AES_KEY = "0x6615171DA4E596F5511B1A445ADDDCA27A31A67246C30B0743F5739E7670D699"

AUTH_TOKEN = "INSERT YOUR TOKEN HERE" # https://github.com/MixV2/EpicResearch/blob/master/docs/auth/grant_types/authorization_code.md

logging.getLogger("UE4Parse").setLevel(logging.INFO)
logging.getLogger("DLManager").setLevel(logging.INFO)
logging.getLogger("DLManager").addHandler(logging.StreamHandler())


def get_provider():
    provider = DefaultFileProvider([os.path.join(FORTNITE_LOCATION, "FortniteGame\Content\Paks\pakChunkEarly-WindowsClient.pak")])
    provider.initialize()
    provider.submit_key(FGuid.default(), FAESKey(AES_KEY))
    return provider

def main():
    provider = get_provider()
    mappings_file = provider.get_reader("FortniteGame/Config/Windows/CosmeticBundleMapping.ini")

    os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)
    with open(os.path.join(DOWNLOAD_LOCATION, "cosmetic_mappings.ini"), "wb") as f:
        f.write(mappings_file.read())

    config = IniOpen(os.path.join(DOWNLOAD_LOCATION, "cosmetic_mappings.ini"))

    bundles = config.read(COSMETIC_ID, "Bundles")
    if bundles is None:
        print("bundle not found")
        exit(1)

    base_url = "https://download.epicgames.com/Builds/Fortnite/Content/CloudDir"
    manifest = "https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/public/assets/Windows/5cb97847cee34581afdbc445400e2f77/FortniteContentBuilds"
    buildinfo = os.path.join(FORTNITE_LOCATION, "Cloud\BuildInfo.ini")

    if not os.path.exists(buildinfo):
        print("BuildInfo.ini not found")
        exit(1)

    buildinfo_config = IniOpen(buildinfo)
    label = buildinfo_config.read('Content', "Label")

    content_manifest = requests.get(manifest, params = {"label": label}, headers={"Authorization": "Bearer " + AUTH_TOKEN})
    if content_manifest.status_code != 200:
        print(content_manifest.text)
        exit(1)
    content_manifest = content_manifest.json()

    manifest_url = content_manifest["items"]["MANIFEST"]["distribution"] + content_manifest["items"]["MANIFEST"]["path"]

    manifest = Manifest.read_all(requests.get(manifest_url).content)

    downloader = DLManager(DOWNLOAD_LOCATION, base_url, "./cache")
    downloader.run_analysis(manifest, None, processing_optimization=True, file_install_tag=bundles)
    taskstoremove = []
    for task in downloader.tasks:
        if isinstance(task, FileTask) and task.flags == TaskFlags.DELETE_FILE | TaskFlags.SILENT:
            taskstoremove.append(task)

    for task in taskstoremove:
        downloader.tasks.remove(task)

    downloader.run()

if __name__ == "__main__":
    main()
    exit(0)
