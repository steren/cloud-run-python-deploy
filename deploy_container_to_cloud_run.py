import os
from google.cloud import run_v2

def check_cloud_run_service_exists(
    project_id: str, 
    region: str, 
    service_name: str
) -> bool:
    """
    Check if a Cloud Run service already exists.
    
    Args:
        project_id (str): Google Cloud Project ID
        region (str): GCP region to check
        service_name (str): Name of the Cloud Run service
    
    Returns:
        bool: True if service exists, False otherwise
    """
    client = run_v2.ServicesClient()
    
    try:
        parent = f"projects/{project_id}/locations/{region}"
        service_path = f"{parent}/services/{service_name}"
        
        # Attempt to get the service
        client.get_service(name=service_path)
        print(f"Cloud Run service {service_name} already exists.")
        return True
    except Exception:
        print(f"Cloud Run service {service_name} does not exist.")
        return False

def deploy_to_cloud_run(
    project_id: str, 
    region: str, 
    service_name: str, 
    image_url: str
):
    """
    Deploy or update a container to Google Cloud Run.
    
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
    
    # Check if service exists
    parent = f"projects/{project_id}/locations/{region}"
    service_path = f"{parent}/services/{service_name}"
    
    try:
        if check_cloud_run_service_exists(project_id, region, service_name):
            service.name = service_path
            # Update existing service
            print(f"🔄 Updating existing service {service_name}...")
            operation = client.update_service(
                service=service
            )
        else:
            # Create new service
            print(f"🆕 Creating new service {service_name}...")
            operation = client.create_service(
                parent=parent, 
                service=service, 
                service_id=service_name
            )
        
        # Wait for operation to complete
        print(f"🚢 Deploying {service_name} to Cloud Run...")
        result = operation.result()
        
        print(f"✅ Service deployed/updated successfully: {result.uri}")
        return result
    
    except Exception as e:
        print(f"❌ Error deploying/updating service: {e}")
        raise

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
