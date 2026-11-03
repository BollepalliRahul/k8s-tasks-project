# Project notes

## Baseline (Docker Compose)
- /health returned {"status":"ok"}
- POST /tasks created task id 1
- Problem: DB password is plaintext in docker-compose.yml
- Problem: single container, no self-healing, no scaling