import requests
import zipfile
import io

url = "https://download.mc-packs.net/pack/f7fb61b2a5a641f278bbf9a83859dc7d96f5df39.zip"
response = requests.get(url, allow_redirects=True)
if response.status_code == 200:
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    print("Extracted files:")
    for file_name in zip_file.namelist():
        print(file_name)

    zip_file.close()
else:
    print(f"Failed to download the file. Status code: {response.status_code}")