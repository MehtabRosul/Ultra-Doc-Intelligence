# 🚀 Deployment Guide: Render

This guide outlines how to deploy the **Ultra Doc-Intelligence Backend** to Render.

---

## Option 1: The Easy Way (Blueprints) ✨

I have added a `render.yaml` file to your repository. This allows Render to automatically configure everything for you.

1.  **Log in to Render** and go to your dashboard.
2.  Click **New +** and select **Blueprint**.
3.  Connect your GitHub repository (`Ultra-Doc-Intelligence`).
4.  Render will detect the `render.yaml` file. Click **Apply**.
5.  **Environment Variables**: You will be prompted to enter values for:
    *   `HF_API_TOKEN`: Your HuggingFace API Token.
    *   `AES_SECRET_KEY`: Your generated AES-256 key.
    *   `PYTHON_VERSION`: Set to `3.9.0` (or `3.10.0`).
6.  Click **Approve** or **Deploy**.
7.  Wait for the build to finish. Your URL will be `https://ultra-doc-intelligence-backend.onrender.com`.

---

## Option 2: Manual Setup 🛠️

If you prefer to configure it manually:

1.  **Log in to Render** and go to your dashboard.
2.  Click **New +** and select **Web Service**.
3.  Connect your GitHub repository.
4.  **Name**: `ultra-doc-backend` (or any name).
5.  **Region**: Choose the one closest to you (e.g., Singapore, Frankfurt).
6.  **Branch**: `main`.
7.  **Root Directory**: `backend` (⚠️ Important: Do not leave blank).
8.  **Runtime**: `Python 3`.
9.  **Build Command**: `pip install -r requirements.txt`
10. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
11. **Instance Type**: Free (or Starter).
12. **Environment Variables** (Scroll down to "Advanced"):
    *   Add `PYTHON_VERSION` = `3.9.0`
    *   Add `HF_API_TOKEN` = `...`
    *   Add `AES_SECRET_KEY` = `...`
13. Click **Create Web Service**.

---

## 🔗 Connecting Frontend

Once deployed, copy your new Backend URL (e.g., `https://your-app.onrender.com`) and update your Frontend environment variables on **Vercel**:

*   **VITE_API_URL**: `https://your-app.onrender.com`

**Note**: The free integration on Render spins down after 15 minutes of inactivity. It may take 50 seconds to wake up on the first request.
