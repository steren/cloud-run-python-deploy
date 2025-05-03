# Cloud Run Deployment Script

## Prerequisites
- Google Cloud SDK installed
- `gcloud` CLI configured
- Python 3.8+
- Google Cloud Project set up

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Application Default Credentials (locally):
```bash
gcloud auth application-default login
```

3. Set environment variables:
```bash
export GCP_PROJECT_ID=your-project-id
```

4. Customize the deployment script:
- Update `region`
- Update `service_name`
- Update `image_url`

## Deploy sample container to Cloud Run
```bash
python deploy_to_cloud_run.py
```

## Deploy sources to Cloud Run
```bash
python deploy_sources_to_cloud_run.py
```

