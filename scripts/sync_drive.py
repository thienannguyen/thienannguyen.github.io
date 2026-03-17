#!/usr/bin/env python3
"""
Sync images from Google Drive folders into the repository.

Google Drive structure expected:
    Shared Folder (DRIVE_ROOT_FOLDER_ID)
    ├── Watercolor/
    │   ├── painting1.jpg
    │   └── painting2.png
    ├── Mixed Media/
    │   └── piece1.jpg
    └── Photography/
        └── photo1.jpg

Each subfolder becomes a category on the site.

Authentication — supports two modes (checked in order):

1. OAuth refresh token (for accessing someone else's shared Drive folder):
       GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN

2. Service account (for your own Drive):
       GOOGLE_CREDENTIALS_JSON  (full JSON key as a string)

Common:
    DRIVE_ROOT_FOLDER_ID — the Google Drive folder containing category subfolders
"""

import json
import os
import random
import re
import shutil
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = REPO_ROOT / "assets" / "images" / "categories"
DATA_DIR = REPO_ROOT / "_data"
CATEGORIES_DIR = REPO_ROOT / "categories"

IMAGE_MIMETYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def get_credentials_oauth():
    """Authenticate using OAuth 2.0 refresh token (your personal Google account)."""
    from google.oauth2.credentials import Credentials

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        return None

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return creds


def get_credentials_service_account():
    """Authenticate using a service account JSON key."""
    from google.oauth2 import service_account

    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        creds_file = REPO_ROOT / "credentials.json"
        if creds_file.exists():
            creds_json = creds_file.read_text()
    if not creds_json:
        return None

    creds_data = json.loads(creds_json)
    return service_account.Credentials.from_service_account_info(
        creds_data, scopes=SCOPES
    )


def get_drive_service():
    creds = get_credentials_oauth()
    if creds:
        print("Authenticated via OAuth refresh token")
    else:
        creds = get_credentials_service_account()
        if creds:
            print("Authenticated via service account")

    if not creds:
        print(
            "Error: No credentials found.\n"
            "  Option 1 — Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN\n"
            "  Option 2 — Set GOOGLE_CREDENTIALS_JSON (service account key)"
        )
        sys.exit(1)

    return build("drive", "v3", credentials=creds)


def list_folders(service, parent_id):
    results = (
        service.files()
        .list(
            q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
            orderBy="name",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    return results.get("files", [])


def list_images(service, folder_id):
    mime_filter = " or ".join(f"mimeType='{mt}'" for mt in IMAGE_MIMETYPES)
    query = f"'{folder_id}' in parents and trashed=false and ({mime_filter})"

    all_files = []
    page_token = None
    while True:
        results = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                orderBy="name",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        all_files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    return all_files


def download_file(service, file_id, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def write_categories_yaml(categories):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for cat in categories:
        lines.append(f'- name: "{cat["name"]}"')
        lines.append(f'  slug: "{cat["slug"]}"')
        lines.append(f'  thumbnail: "{cat["thumbnail"]}"')
        lines.append(f"  images:")
        for img in cat["images"]:
            lines.append(f'    - filename: "{img["filename"]}"')
            lines.append(f'      title: "{img["title"]}"')
            lines.append(f'      path: "{img["path"]}"')
    out = DATA_DIR / "categories.yml"
    out.write_text("\n".join(lines) + "\n")
    print(f"Written {out}")


def write_category_pages(categories):
    CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)
    active_slugs = {cat["slug"] for cat in categories}

    for old_page in CATEGORIES_DIR.glob("*.html"):
        if old_page.stem not in active_slugs:
            print(f"Removing stale category page: {old_page.name}")
            old_page.unlink()

    for cat in categories:
        page = CATEGORIES_DIR / f"{cat['slug']}.html"
        page.write_text(
            f"---\n"
            f"layout: category\n"
            f'title: "{cat["name"]}"\n'
            f'category_slug: "{cat["slug"]}"\n'
            f"---\n"
        )
        print(f"Written {page}")


def sync():
    root_folder_id = os.environ.get("DRIVE_ROOT_FOLDER_ID")
    if not root_folder_id:
        print("Error: DRIVE_ROOT_FOLDER_ID not set")
        sys.exit(1)

    service = get_drive_service()
    folders = list_folders(service, root_folder_id)

    if not folders:
        print("No category folders found in the root Drive folder")
        return

    categories = []
    active_slugs = set()

    for folder in folders:
        name = folder["name"]
        slug = slugify(name)
        active_slugs.add(slug)
        cat_dir = IMAGES_DIR / slug
        cat_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nSyncing category: {name} → {slug}/")
        images = list_images(service, folder["id"])

        if not images:
            print("  No images found, skipping")
            continue

        remote_filenames = set()
        image_entries = []

        for img in images:
            filename = img["name"]
            remote_filenames.add(filename)
            dest = cat_dir / filename

            if dest.exists():
                print(f"  Exists, skipping: {filename}")
            else:
                print(f"  Downloading: {filename}")
                download_file(service, img["id"], dest)

            title = dest.stem.replace("-", " ").replace("_", " ").title()
            rel_path = f"/assets/images/categories/{slug}/{filename}"
            image_entries.append(
                {"filename": filename, "title": title, "path": rel_path}
            )

        for local_file in cat_dir.iterdir():
            if local_file.is_file() and local_file.name not in remote_filenames:
                print(f"  Removing deleted file: {local_file.name}")
                local_file.unlink()

        thumbnail = random.choice(image_entries)
        categories.append(
            {
                "name": name,
                "slug": slug,
                "thumbnail": thumbnail["path"],
                "images": image_entries,
            }
        )

    if IMAGES_DIR.exists():
        for local_dir in IMAGES_DIR.iterdir():
            if local_dir.is_dir() and local_dir.name not in active_slugs:
                print(f"\nRemoving deleted category: {local_dir.name}/")
                shutil.rmtree(local_dir)

    write_categories_yaml(categories)
    write_category_pages(categories)
    print(f"\nSync complete — {len(categories)} categories")


if __name__ == "__main__":
    sync()
