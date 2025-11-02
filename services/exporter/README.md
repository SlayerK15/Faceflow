# Faceflow Exporter Service (Stub)

This directory hosts the exporter/sharing worker in the full Faceflow architecture. The current demo implementation keeps sharing logic inside the API service, so this folder simply documents the intended responsibilities:

- Accept share requests from the API or queue
- Build ZIP archives for selected clusters
- Persist bundles to object storage and provide signed URLs
- Notify recipients via email/SNS

Future iterations can move the in-memory bundle handling from the API into a dedicated worker housed here.
