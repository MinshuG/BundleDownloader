import json
import os
from legendary.downloader.mp.manager import DLManager
from legendary.models.downloading import FileTask, TaskFlags
from Ini import IniOpen
from downloader import get_manifest, get_provider, base_url


conf_path = "config.json"

if os.path.exists(conf_path):
    config = json.load(open(conf_path))
else:
    print("config.json not found")
    exit(1)

DOWNLOAD_LOCATION = config["DOWNLOAD_LOCATION"]
FORTNITE_LOCATION = config["FORTNITE_LOCATION"]
COSMETIC_ID = config["cosmetics"]
AES_KEY = config["MAIN_AES_KEY"]
token = config["token"]


def main():
    provider = get_provider(FORTNITE_LOCATION, AES_KEY)
    mappings_file = provider.get_reader("FortniteGame/Config/Windows/CosmeticBundleMapping.ini")
    if mappings_file is None:
        print("CosmeticBundleMapping.ini not found. perhaps outdated aes key?")
        exit(1)

    os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)
    with open(os.path.join(DOWNLOAD_LOCATION, "cosmetic_mappings.ini"), "wb") as f:
        f.write(mappings_file.read())

    cosmetic_mappings = IniOpen(os.path.join(DOWNLOAD_LOCATION, "cosmetic_mappings.ini"))

    bundles = []
    for id in COSMETIC_ID:
        tags = cosmetic_mappings.read(id, "Bundles")
        if tags is None:
            print(id, "not found")
            continue
        bundles.extend(tags)
    bundles = list(set(bundles)) # remove duplicates

    if len(bundles) == 0:
        print("bundles not found")
        exit(1)
    if token is None:
        override_url = config["ContentManifestURL"]
    else:
        override_url = None

    manifest = get_manifest(FORTNITE_LOCATION, token, override_url=override_url)
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
