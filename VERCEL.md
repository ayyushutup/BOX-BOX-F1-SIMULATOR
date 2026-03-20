# Vercel Frontend Deployment

This project should be deployed to Vercel as **frontend-only**.
Backend stays on your Docker host.

## 1) Push latest code
```bash
cd "/Users/ayushrthakur/Documents/BOX BOX"
git add .
git commit -m "Add Vercel frontend deployment config"
git push
```

## 2) Create Vercel project
1. Go to Vercel dashboard.
2. Import your GitHub repo.
3. Keep root as repo root (the `vercel.json` handles frontend paths).

## 3) Set environment variable
In Vercel Project Settings -> Environment Variables, add:

- `VITE_API_BASE_URL` = `https://<your-backend-domain>`

Example:
- `VITE_API_BASE_URL=https://boxbox.duckdns.org`

## 4) Deploy
Click Deploy in Vercel.

## 5) Verify
- Open Vercel URL.
- Start a simulation.
- Confirm browser network calls go to your backend domain (`/api/scenarios/predict` on backend host).

## 6) Add custom domain (optional)
1. Project Settings -> Domains -> add your domain/subdomain.
2. Update DNS records as shown by Vercel.
