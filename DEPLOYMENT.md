# Deployment Guide - Anestesidoseringshjälp

## Deploying to Streamlit Community Cloud (FREE)

Follow these steps to deploy your app for free on Streamlit Community Cloud:

### Prerequisites
- GitHub account (create one at https://github.com if you don't have one)
- Streamlit Community Cloud account (sign up at https://streamlit.io/cloud)

### Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `anestesidoseringshjalp`)
3. Choose **Public** (required for free Streamlit deployment)
4. Don't initialize with README (we already have files)

### Step 2: Push Your Code to GitHub

Run these commands in your terminal:

```bash
# Add the GitHub remote (replace YOUR_USERNAME and YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Check what will be committed
git status

# Commit your changes
git add .
git commit -m "Initial commit - Anesthesia dosing assistant"

# Push to GitHub
git push -u origin master
```

### Step 3: Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select:
   - **Repository**: Your GitHub repo
   - **Branch**: master
   - **Main file path**: oxydos_v8.py
5. Click **"Advanced settings"** and add secrets:
   ```toml
   [admin]
   password_hash = "your_bcrypt_hash_here"
   ```
   To generate a password hash, run locally:
   ```python
   import bcrypt
   password = b"your_desired_password"
   hash = bcrypt.hashpw(password, bcrypt.gensalt())
   print(hash.decode())
   ```
6. Click **"Deploy"**

### Step 4: Wait for Deployment

The app will take 2-5 minutes to deploy. You'll get a public URL like:
`https://your-app-name.streamlit.app`

### Important Notes

- **Database**: The app starts with an empty database on Streamlit Cloud. It will learn from usage.
- **Free Tier Limits**:
  - App goes to sleep after inactivity
  - 1 GB RAM
  - CPU resources shared
- **Security**: Never commit database.json or secrets.toml to GitHub!

### Troubleshooting

If deployment fails:
1. Check the logs in Streamlit Cloud dashboard
2. Verify all dependencies are in requirements.txt
3. Ensure oxydos_v8.py is in the root directory
4. Check that secrets are properly configured

### Updating Your App

To deploy updates:
```bash
git add .
git commit -m "Your update message"
git push
```

Streamlit Cloud will automatically redeploy!

## Alternative Free Hosting Options

### Railway.app
- Free tier: 500 hours/month
- Better for apps with higher resource needs
- Deployment: https://railway.app/

### Render.com
- Free tier available
- Good for production apps
- Deployment: https://render.com/

### Hugging Face Spaces
- Free hosting for ML apps
- Integrated with Streamlit
- Deployment: https://huggingface.co/spaces
