
# 📘 HMC-RMOB Version Lookup API

## 📌 Overview

This is a **Flask-based API** that enables users to **lookup HMC versions and RMOB regions** using HERE Data API.  
It fetches and **caches PBF data** in memory to improve query performance, reducing redundant API calls.

## 🛠 Requirements

- **Python 3.8+**
- Required Python libraries:
  ```sh
  pip install requests flask google.protobuf requests_oauthlib
  ```
- **HERE Data API Credentials**

## 🔐 Configuration

The API requires HERE Data API OAuth2 credentials. You can set them using:

### **Option 1: Environment Variables**
```sh
export HERE_CLIENT_ID="your_client_id"
export HERE_CLIENT_SECRET="your_client_secret"
export HERE_TOKEN_URL="https://account.api.here.com/oauth2/token"
```

### **Option 2: `credential.properties`**
```ini
here.token.endpoint.url = https://account.api.here.com/oauth2/token
here.access.key.id = your_client_id
here.access.key.secret = your_client_secret
```
📌 The API prioritizes environment variables first, then falls back to `credential.properties`.

## 🚀 Running the API

Start the API locally:
```sh
python flask_api.py
```
If successful, it will be available at:
```
http://0.0.0.0:10000/
```

## 🔄 API Endpoints

### **1️⃣ Lookup HMC Version**
**`GET /lookup?hmc_version=<int>[&rmob_region=<str>]`**  
Retrieves the corresponding `region` & `dvn` for a given `hmc_version`.

**Example:**
```sh
curl "http://localhost:10000/lookup?hmc_version=6939"
```

### **2️⃣ Reverse Lookup HMC Version**
**`GET /reverse-lookup?dvn=<str>[&rmob_region=<str>]`**  
Retrieves the `min_version`, `max_version`, and catalog details for a given `dvn`.

**Example:**
```sh
curl "http://localhost:10000/reverse-lookup?dvn=24151"
```

### **3️⃣ Health Check**
**`GET /health`**  
Verifies if the API is running.

```sh
curl "http://localhost:10000/health"
```

## 🌍 Deploying to Render

1. Create a **`render.yaml`** file:
```yaml
services:
  - type: web
    name: hmc-rmob-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python flask_api.py"
    envVars:
      - key: HERE_CLIENT_ID
        sync: false
      - key: HERE_CLIENT_SECRET
        sync: false
      - key: HERE_TOKEN_URL
        value: "https://account.api.here.com/oauth2/token"
```
2. Push the code to **GitHub**:
```sh
git init
git add .
git commit -m "Initial commit"
git push origin main
```
3. Deploy on **[Render.com](https://dashboard.render.com/)**.

## ✅ Summary

- **HMC version → region lookup**
- **DVN reverse lookup**
- **Cached PBF data for performance**
- **Deployable to Render with memory-based caching**
- **REST API for easy integration**

🚀 **Your API is now ready to use!**

![](https://i.imgur.com/sGNvpbO.png)

![](https://i.imgur.com/Qoglqqc.png)