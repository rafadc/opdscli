import time
from pathlib import Path

import httpx
from rich.progress import Progress, TaskID

from opdscli.config import CatalogConfig


class OPDSClientError(Exception):
    pass


def create_client(
    catalog: CatalogConfig, timeout: float = 30.0,
) -> httpx.Client:
    """Create an httpx client with auth for the given catalog."""
    auth = None
    headers: dict[str, str] = {}

    if catalog.auth:
        if (
            catalog.auth.type == "basic"
            and catalog.auth.username
            and catalog.auth.password
        ):
            auth = httpx.BasicAuth(
                catalog.auth.username, catalog.auth.password,
            )
        elif catalog.auth.type == "bearer" and catalog.auth.token:
            headers["Authorization"] = (
                f"Bearer {catalog.auth.token}"
            )

    return httpx.Client(
        auth=auth, headers=headers,
        timeout=timeout, follow_redirects=True,
    )


def fetch_url(client: httpx.Client, url: str) -> str:
    """Fetch a URL with retry-once-with-backoff."""
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = client.get(url)
            if response.status_code in (401, 403):
                raise OPDSClientError(
                    f"Authentication failed "
                    f"({response.status_code}). "
                    f"Check your credentials."
                )
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            raise OPDSClientError(
                f"HTTP error {e.response.status_code}: "
                f"{e.response.reason_phrase}"
            ) from e
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.ReadError,
        ) as e:
            last_error = e
            if attempt == 0:
                time.sleep(1.0)

    raise OPDSClientError(
        f"Network error after retry: {last_error}",
    )


def stream_download(
    client: httpx.Client,
    url: str,
    dest: Path,
    progress: Progress,
    task_id: TaskID,
) -> None:
    """Download a file with streaming and progress updates."""
    with client.stream("GET", url) as response:
        response.raise_for_status()
        total = response.headers.get("content-length")
        if total:
            progress.update(task_id, total=int(total))

        with open(dest, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=8192):
                f.write(chunk)
                progress.advance(task_id, len(chunk))
