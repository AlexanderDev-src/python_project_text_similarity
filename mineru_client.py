import os
import time
import requests


class MinerUClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://mineru.net/api/v4"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def upload_file(self, file_path_or_content, filename):
        """
        Uploads a file to MinerU and returns the download URL or File ID.
        """
        # 1. Get Upload URL
        url = f"{self.base_url}/file-urls/batch"
        data = {"files": [{"name": filename}]}

        print(f"Requesting upload URL for {filename}...")
        resp = requests.post(url, headers=self.headers, json=data)
        if resp.status_code != 200 or resp.json().get("code") != 0:
            raise Exception(f"Failed to get upload URL: {resp.text}")

        data = resp.json().get("data", {})
        file_urls = data.get("file_urls", [])
        if not file_urls:
            raise Exception(f"No upload URLs returned: {resp.text}")

        upload_url = file_urls[0]
        # The key to use for extraction might be the signedUrl itself or we might need to rely on what this returns.
        # Usually for signed URL uploads, we PUT to the URL.

        # 2. Upload Content
        print(f"Uploading content to {upload_url[:50]}...")
        headers_upload = {}  # Try without Content-Type as per docs

        # Determine if file_path_or_content is path or bytes
        if isinstance(file_path_or_content, str) and os.path.exists(
            file_path_or_content
        ):
            with open(file_path_or_content, "rb") as f:
                upload_resp = requests.put(upload_url, data=f, headers=headers_upload)
        else:
            upload_resp = requests.put(
                upload_url, data=file_path_or_content, headers=headers_upload
            )

        if upload_resp.status_code != 200:
            raise Exception(
                f"Failed to upload file content: {upload_resp.status_code} {upload_resp.text}"
            )

        # Return the URL that MinerU can access.

        return upload_url

    def _process_url(self, url):
        """
        Pre-process the URL to handle common issues (e.g., converting Google Drive viewer links).
        """
        import re

        # Handle Google Drive Viewer Links
        # Pattern: https://drive.google.com/file/d/{FILE_ID}/view...
        gdrive_pattern = r"https://drive\.google\.com/file/d/([-_\w]+)"
        match = re.search(gdrive_pattern, url)
        if match:
            file_id = match.group(1)
            print(f"DEBUG: Detected Google Drive File ID: {file_id}")

            try:
                # 1. Try to get the confirmation code
                confirm_url = (
                    f"https://drive.google.com/uc?export=download&id={file_id}"
                )
                session = requests.Session()
                response = session.get(confirm_url, stream=True)

                # Check if we got a warning page (status 200 and text/html)
                if "text/html" in response.headers.get("Content-Type", "").lower():
                    # Look for the confirmation token in the page or cookies
                    for key, value in session.cookies.items():
                        if key.startswith("download_warning"):
                            print(f"DEBUG: Found download warning token: {value}")
                            new_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={value}"
                            return new_url

                    # Alternatively, sometimes it's in the 'confirm' query param of the link in the HTML
                    # But simpler to just return the confirm=t attempt if we can't find specific token
                    pass
            except Exception as e:
                print(f"DEBUG: Error trying to resolve GDrive link: {e}")

            # Fallback to simple confirm=t
            new_url = (
                f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
            )
            return new_url

        return url

    def extract(self, file_url, is_ocr=True):
        # Pre-process URL (e.g. handle Google Drive)
        clean_url = self._process_url(file_url)

        url = f"{self.base_url}/extract/task"
        data = {
            "url": clean_url,
            "model_version": "vlm",
            "is_ocr": is_ocr,
            "language": "th",
        }
        print(f"Submitting extraction task for {clean_url[:50]}...")
        resp = requests.post(url, headers=self.headers, json=data)

        if resp.status_code != 200 or resp.json().get("code") != 0:
            raise Exception(f"Failed to submit extraction task: {resp.text}")

        task_id = resp.json()["data"]["task_id"]
        return task_id

    def poll_task(self, task_id, timeout=300):
        start_time = time.time()
        print(f"Polling task {task_id}...")
        while time.time() - start_time < timeout:
            query_url = f"{self.base_url}/extract/task/{task_id}"
            resp = requests.get(query_url, headers=self.headers)
            data = resp.json()

            if "data" in data and "state" in data["data"]:
                state = data["data"]["state"]
                if state == "done":
                    return data["data"]
                elif state == "failed":
                    raise Exception(f"Task failed: {data}")

            time.sleep(2)
        raise Exception("Task timed out")
