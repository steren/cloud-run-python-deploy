import os
from google.cloud import run_v2

def deploy_to_cloud_run(
    project_id: str, 
    region: str, 
    service_name: str, 
    image_url: str
):
    """
    Deploy a container to Google Cloud Run.
    
    Args:
        project_id (str): Google Cloud Project ID
        region (str): GCP region to deploy to
        service_name (str): Name of the Cloud Run service
        image_url (str): Full URL of the container image
    """
    # Initialize Cloud Run client
    client = run_v2.ServicesClient()
    
    # Prepare service configuration
    service = run_v2.Service()
    service.invoker_iam_disabled = True
    
    # Configure container
    container = run_v2.Container()
    container.image = image_url
    
    service.template.containers = [container]
    
    # Deploy the service
    parent = f"projects/{project_id}/locations/{region}"
    operation = client.create_service(
        parent=parent, 
        service=service, 
        service_id=service_name
    )
    
    # Wait for deployment to complete
    print(f"Deploying {service_name} to Cloud Run...")
    result = operation.result()
    
    print(f"Service deployed successfully: {result.uri}")
    return result

def main():
    # Example usage - replace with your actual values
    project_id = os.environ.get('GCP_PROJECT_ID')
    region = 'us-central1'
    service_name = 'my-cloud-run-service'
    image_url = 'gcr.io/cloudrun/hello:latest'
    
    deploy_to_cloud_run(
        project_id=project_id,
        region=region,
        service_name=service_name,
        image_url=image_url
    )

if __name__ == '__main__':
    main()
