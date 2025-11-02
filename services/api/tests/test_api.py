import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from fastapi.testclient import TestClient

from services.api.app.main import app


client = TestClient(app)


def test_album_lifecycle():
    album_resp = client.post("/albums", json={"name": "Summer"})
    assert album_resp.status_code == 201
    album = album_resp.json()

    photo_payload = {
        "filename": "img1.jpg",
        "embedding": [1.0, 0.0, 0.0],
        "metadata": {"camera": "phone"},
    }
    photo_resp = client.post(f"/albums/{album['id']}/photos", json=photo_payload)
    assert photo_resp.status_code == 201

    photo_payload["filename"] = "img2.jpg"
    photo_payload["embedding"] = [0.9, 0.1, 0.0]
    client.post(f"/albums/{album['id']}/photos", json=photo_payload)

    cluster_resp = client.post(f"/albums/{album['id']}/cluster")
    assert cluster_resp.status_code == 200
    clusters = cluster_resp.json()
    assert len(clusters) == 1

    bundle_resp = client.post(
        "/share",
        json={
            "album_id": album["id"],
            "cluster_ids": [clusters[0]["id"]],
            "recipients": ["alice@example.com"],
        },
    )
    assert bundle_resp.status_code == 201
    bundle = bundle_resp.json()

    fetch_bundle = client.get(f"/share/{bundle['id']}")
    assert fetch_bundle.status_code == 200
    assert fetch_bundle.json()["id"] == bundle["id"]
