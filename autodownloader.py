
import base64
import json
import os
import sys
import requests
from legendary.models.manifest import Manifest
from legendary.downloader.mp.manager import DLManager

from Ini import IniOpen

client = "ec684b8c687f479fadea3cb2ad83f5c6"
secret = "e1f31c211f28413186262d37a13fc84d"
fortClientPC_token = base64.b64encode(bytes(f"{client}:{secret}".encode("ascii"))).decode("ascii")
CREDENTIAL_URL = "https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/token"
EGS_TOKEN = f"basic {base64.b64encode(bytes('3446cd72694c4a4485d81b77adbb2141:9209d4a5e25a457fb9b07489d313b41a'.encode('ascii'))).decode('ascii')}"

# no comments on code quality pls
USE_NEW_MANIFEST = True
if USE_NEW_MANIFEST:
    def getSignedDownloadUrl(platform, catalogItemId, namespace, appName, label, clientDetails): # ??
        base = "https://launcher-public-service-prod06.ol.epicgames.com/launcher/"
        ep = f"api/public/assets/v2/platform/{platform}/namespace/{namespace}/catalogItem/{catalogItemId}/app/{appName}/label/{label}"
        return f"{base}{ep}"
    MANIFEST_URL = getSignedDownloadUrl("Windows", "4fe75bbc5a674f4f9b356b5c90567da5", "fn", "Fortnite", "Live", {})

    # MANIFEST_URL = "https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/public/assets/v2/platform/Windows/namespace/fn/catalogItem/4fe75bbc5a674f4f9b356b5c90567da5/app/Fortnite/label/Live" # signed?
else:
    MANIFEST_URL = "https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/public/assets/Windows/4fe75bbc5a674f4f9b356b5c90567da5/Fortnite" # old?

def get_token(creds=EGS_TOKEN):
    header = {"Content-Type": "application/x-www-form-urlencoded",
              "Authorization": creds}
    CLIENT_POST_DATA = "grant_type=client_credentials&token_token=eg1"
    manifest = requests.post(CREDENTIAL_URL, headers=header, data=CLIENT_POST_DATA)
    return manifest.json()['access_token']

def get_manifest_info(token, manifest_url, label="Live"):
    header = {"Authorization": f'bearer {token}'}
    data = requests.get(manifest_url, headers=header,  params = {"label": label})
    if data.status_code != 200:
        print("Failed to get manifest info")
        sys.exit(1)

    resp_json = data.json()
    with open("temp/manifest_info.json", "w") as f:
        json.dump(resp_json, f, indent=4)

    return data.json()

def get_chunk_manifest(manifest_file):
    if "elements" in manifest_file:
        for element in manifest_file["elements"]:
            if element["appName"] == "Fortnite":
                for distribution in element["manifests"]:
                    uri = distribution["uri"]
                    params = { k["name"]:k["value"] for k in distribution["queryParams"]}
                    manifest = requests.get(uri, params=params)
                    if manifest.status_code == 200:
                        break
                    else:
                        print(f"Failed to get manifest({uri}), retrying")
    else:
        for distribution in [manifest_file["items"]["MANIFEST"]["distribution"]]+ manifest_file["items"]["MANIFEST"]["additionalDistributions"]:
            uri = distribution + manifest_file["items"]["MANIFEST"]["path"]
            manifest = requests.get(uri, params=manifest_file["items"]["MANIFEST"]["signature"])
            if manifest.status_code == 200:
                break
            else:
                print(f"Failed to get manifest({distribution}), retrying")
    if manifest.status_code != 200:
        print("Failed to get manifest")
        sys.exit(1)
    return manifest.content

def get_build_info():
    token = get_token()
    manifest = get_manifest_info(token, MANIFEST_URL)
    chunk_manifest = get_chunk_manifest(manifest)
    if USE_NEW_MANIFEST:
        version = manifest["elements"][0]["buildVersion"]
    else:
        version = manifest['buildVersion']
    manifest = Manifest.read_all(chunk_manifest)

    downloader = DLManager("./temp", "https://epicgames-download1.akamaized.net/Builds/Fortnite/CloudDir/", "./cache")
    downloader.run_analysis(manifest, None, processing_optimization=True, file_prefix_filter="Cloud/BuildInfo.ini")

    try:
        downloader.run()
        # exec("downloader.run()", globals(), locals())
    except SystemExit as e:
        pass

    if os.path.exists("./temp/Cloud/BuildInfo.ini"):
        return IniOpen("./temp/Cloud/BuildInfo.ini"), version
    else:
        print("BuildInfo.ini not found")
        sys.exit(1)


def get_token_fn():
    return fortClientPC_token


def get_content_manifest(token, label):
    manifest = get_manifest_info(token,
                                 "https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/public/assets/Windows/5cb97847cee34581afdbc445400e2f77/FortniteContentBuilds", label=label)
    return manifest


def do_rest_stuff(content_manifest, fn_version):
    """download it if it doesn't exist and create a entry in readme"""

    filename = os.path.basename(content_manifest['items']['MANIFEST']['path'])
    path = os.path.join("ContentManifests", filename)
    if not os.path.exists(path):
        chunk_manifest = get_chunk_manifest(content_manifest)
        with open(path, "wb") as f:
            f.write(chunk_manifest)
        s = "|{}|{}|[Manifest](https://github.com/MinshuG/BundleDownloader/blob/master/ContentManifests/{}?raw=true)|".format(fn_version, filename[:-9], filename)
        with open("ContentManifests\README.md", "a") as f:
            f.write(s + "\n")
        print("Successfully added {} for {}".format(filename, fn_version))

        env_file = os.getenv('GITHUB_ENV')
        if env_file:
            with open(env_file, "a") as myfile:
                myfile.write("has_updated=True\n")
        else:
            print("GITHUB_ENV not set")
    else:
        print("{} already exists".format(filename))

def main():
    os.makedirs("temp", exist_ok=True)
    buildinfo, version = get_build_info()
    print("Build:", buildinfo.read("Content", "Build"))
    label = buildinfo.read("Content", "Label")[0]
    print("Label:", label)

    auth_token = get_token()
    do_rest_stuff(get_content_manifest(auth_token, label=label), version)

if __name__ == "__main__":
    main()
