import requests
from urllib.parse import urlparse
import json
import pprint
import os


BLOCKLIST = "data/input/centers_blocklist.json"
GITHUB_BLOCKLIST = f"https://raw.githubusercontent.com/CovidTrackerFr/vitemadose/data-auto/{BLOCKLIST}"
GITLAB_CENTERS = f"https://vitemadose.gitlab.io/vitemadose/info_centres.json"


def input_url():
    url_to_delete = os.environ.get("INPUT_URL_TO_DELETE", "")
    return url_to_delete


def is_url_in_json(url_to_delete: str):
    url_in_json = False
    center_data = None
    url_path = urlparse(url_to_delete).path
    filtered_json = filter_urls()
    for centre in filtered_json:
        if url_path in centre["url"]:
            url_in_json = True
            center_data = centre
    return url_in_json, center_data


def filter_urls():
    new_centres = []
    response = requests.get(GITLAB_CENTERS)
    response.raise_for_status()
    centers_list = response.json()

    for departement, centers in centers_list.items():
        for available in centers["centres_disponibles"]:
            new_centres.append(available)
        for unavailable in centers["centres_indisponibles"]:
            new_centres.append(unavailable)
    return new_centres


def update_json(center_data, github_issue, delete_reason):

    url_path = urlparse(center_data["url"]).path

    with open(GITHUB_BLOCKLIST, "r+") as blocklist_file:

        data = json.load(blocklist_file)
        print(data)
        new_center = {
            "name": center_data["nom"],
            "url": center_data["url"],
            "issue": github_issue,
            "details": delete_reason,
        }
        for blocked_center in data["centers_not_displayed"]:
            if url_path in blocked_center["url"]:
                print("[ERREUR] - Le centre est déjà bloqué.")
                exit(1)

        data["centers_not_displayed"].append(new_center)
        blocklist_file.seek(0)
        
        json.dump(data, blocklist_file, indent=2)
        print("\n[SUCCESS] - Le centre a bien été ajouté à la blocklist !\n")


def main():

    delete_reason = None
    github_issue = None

    print("\n******************* BLOCKLIST MANAGER *******************")
    print("Ce programme permet d'ajouter ou supprimer un centre à la Blocklist")

    url_to_delete = input_url()
    url_in_json, center_data = is_url_in_json(url_to_delete)

    if url_in_json:
        delete_reason = (
            os.environ.get("INPUT_URL_TO_DELETE", "").strip()
            if len(os.environ.get("INPUT_URL_TO_DELETE", "")) > 0
            else None
        )
        github_issue = (
            os.environ.get("INPUT_GIT_ISSUE", "").strip() if len(os.environ.get("INPUT_GIT_ISSUE", "")) > 0 else None
        )

        update_json(center_data, github_issue, delete_reason)
    else:
        print("[ERREUR] - Ce centre n'est pas présent dans nos fichiers.")
        exit(1)


if __name__ == "__main__":
    # execute only if run as a script
    main()
