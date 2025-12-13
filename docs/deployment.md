# Deployment Guide

This guide covers deploying the URDB Tariff Viewer application to various platforms.

## Prerequisites

- GitHub account (for Streamlit Cloud deployment)
- Basic familiarity with command line/terminal
- Your app code ready for deployment

## Deployment Options

### Option 1: Streamlit Cloud (Recommended) ⭐

**Pros:** Free, easiest setup, optimized for Streamlit apps
**Cons:** Limited customization, may have usage limits

#### Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Set main file path to `streamlit_app.py`
   - Click "Deploy"

3. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to Settings → Secrets
   - Add your `OPENEI_API_KEY` if needed

### Option 2: Heroku

**Pros:** Free tier available, more customization
**Cons:** Requires more configuration

#### Steps:

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Heroku App**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Ensure Procfile exists**
   ```
   web: streamlit run streamlit_app.py --server.port $PORT --server.headless true
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

### Option 3: Docker

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.headless=true"]
```

#### Build and Run
```bash
docker build -t urdb-viewer .
docker run -p 8501:8501 urdb-viewer
```

### Option 4: Cloud Platforms (AWS/GCP/Azure)

For production deployments, consider:

- **AWS**: EC2, ECS, or App Runner
- **Google Cloud**: Cloud Run or Compute Engine
- **Azure**: App Service or Container Instances

## Configuration Files

Your app includes these deployment-ready files:

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `.streamlit/config.toml` | Streamlit configuration |
| `Procfile` | Heroku process definition |
| `pyproject.toml` | Package metadata |

## Testing Your Deployment

After deployment, verify:

1. **Functionality**
   - Tariff selection works
   - Visualizations render
   - Cost calculator functions
   - Dark/light mode toggle

2. **Performance**
   - Acceptable load times
   - Responsive UI

3. **Cross-device**
   - Desktop browsers
   - Mobile devices

## Security Considerations

- App is publicly accessible by default
- Use Streamlit secrets for API keys
- Consider authentication for sensitive deployments
- Monitor usage and set rate limits if needed

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENEI_API_KEY` | OpenEI API access |
| `ENVIRONMENT` | development/production |
| `DEBUG` | Enable debug mode |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No JSON files found" | Ensure `data/` directory is deployed |
| Import errors | Verify all dependencies in requirements.txt |
| Memory issues | Optimize data loading, use caching |
| Timeout errors | Reduce initial data load |

## Support

- **Streamlit**: [docs.streamlit.io](https://docs.streamlit.io)
- **Heroku**: [devcenter.heroku.com](https://devcenter.heroku.com)
