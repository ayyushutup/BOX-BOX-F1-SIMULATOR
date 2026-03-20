# BOX BOX Deploy Guide

## 1) Server prerequisites (Ubuntu)
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git curl
sudo usermod -aG docker $USER
```
Log out and back in once after adding docker group.

## 2) Clone and configure
```bash
git clone <YOUR_REPO_URL> "BOX BOX"
cd "BOX BOX"
cp .env.example .env
```

Edit `.env`:
- `POSTGRES_PASSWORD` must be a real secure password.
- `CORS_ORIGINS` should include your production domain(s).

Example:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_this_to_a_strong_secret
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
GUNICORN_TIMEOUT=120
LOG_LEVEL=info
```

## 3) Deploy
```bash
./deploy.sh
```

## 4) Verify
```bash
docker compose ps
docker compose logs -f backend
curl http://localhost/health
curl http://localhost/api/tracks
```

## 5) Update deployment
```bash
git pull
./deploy.sh
```
