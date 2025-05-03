import os
import zipfile
from typing import List
from google.cloud.devtools import cloudbuild_v1
from google.cloud import run_v2, storage
from google.cloud import artifactregistry_v1
from google.cloud.storage import Client as StorageClient
from google.cloud.artifactregistry_v1 import ArtifactRegistryClient
from google.cloud.artifactregistry_v1.types import Repository
from google.cloud.storage import Bucket
from google.cloud.devtools.cloudbuild_v1.types import (
    StorageSource, 
    Source, 
    Build, 
    BuildStep
)

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

def check_storage_bucket_exists(project_id: str, bucket_name: str):
    """
    Check if a Google Cloud Storage bucket already exists.
    
    Args:
        project_id (str): Google Cloud Project ID
        bucket_name (str): Name of the bucket to check
    
    Returns:
        bool: True if bucket exists, False otherwise
    """
    storage_client = storage.Client(project=project_id)
    
    try:
        bucket = storage_client.get_bucket(bucket_name)
        print(f"🗃️ Bucket {bucket_name} already exists.")
        return True
    except Exception:
        print(f"❌ Bucket {bucket_name} does not exist.")
        return False

def create_storage_bucket(project_id: str, bucket_name: str, location: str = 'us'):
    """ 
    Create a new Google Cloud Storage bucket.
    
    Args:
        project_id (str): Google Cloud Project ID
        bucket_name (str): Name of the bucket to create
        location (str, optional): Bucket location. Defaults to 'us'.
    
    Returns:
        Bucket: The created storage bucket
    """
    storage_client = storage.Client(project=project_id)
    
    try:
        print(f"Attempting to create storage bucket {bucket_name} in location {location}...")
        bucket = storage_client.create_bucket(bucket_name, location=location)
        print(f"✅ Storage bucket {bucket_name} created successfully in {location}.")
        return bucket
    except Exception as e:
        print(f"❌ Failed to create storage bucket {bucket_name}. Error details: {e}")
        return None

def zip_local_folder(folder_path: str, output_zip: str):
    """
    Zip a local folder.
    
    Args:
        folder_path (str): Path to the folder to zip
        output_zip (str): Path to the output zip file
    
    Returns:
        str: Path to the created zip file
    """
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname=arcname)
    
    print(f"📦 Folder {folder_path} zipped to {output_zip}")
    return output_zip

def upload_to_storage_bucket(bucket: Bucket, zip_file_path: str, destination_blob_name: str):
    """
    Upload a file to a Google Cloud Storage bucket.
    
    Args:
        bucket (Bucket): The storage bucket to upload to
        zip_file_path (str): Path to the local file to upload
        destination_blob_name (str): Name of the blob in the bucket
    
    Returns:
        Blob: The uploaded blob
    """
    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(zip_file_path)
        print(f"📤 File {zip_file_path} uploaded to {destination_blob_name}")
        return blob
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        return None

def check_artifact_registry_repo_exists(project_id: str, region: str, repo_name: str):
    """
    Check if an Artifact Registry repository already exists.
    
    Args:
        project_id (str): Google Cloud Project ID
        region (str): GCP region for the repository
        repo_name (str): Name of the repository
    
    Returns:
        bool: True if repository exists, False otherwise
    """
    client = ArtifactRegistryClient()
    
    parent = f"projects/{project_id}/locations/{region}"
    
    try:
        # List repositories and check if the specific repo exists
        request = artifactregistry_v1.ListRepositoriesRequest(parent=parent)
        repositories = client.list_repositories(request=request)
        
        for repo in repositories:
            if repo.name.split('/')[-1] == repo_name:
                print(f"🏺 Repository {repo_name} already exists.")
                return True
        
        print(f"❌ Repository {repo_name} does not exist.")
        return False
    except Exception as e:
        print(f"❗ Error checking repository {repo_name}: {e}")
        return False

def create_artifact_registry_repo(project_id: str, region: str, repo_name: str, format: str = 'DOCKER'):
    """ 
    Create an Artifact Registry repository.
    
    Args:
        project_id (str): Google Cloud Project ID
        region (str): GCP region for the repository
        repo_name (str): Name of the repository
        format (str, optional): Repository format. Defaults to 'DOCKER'.
    
    Returns:
        Repository: The created repository
    """
    client = ArtifactRegistryClient()
    
    parent = f"projects/{project_id}/locations/{region}"
    repo = artifactregistry_v1.Repository(
        format_=format,
        repository_id=repo_name
    )
    
    try:
        print(f"🏗️ Preparing to create Artifact Registry repository {repo_name} in {region}...")
        operation = client.create_repository(
            parent=parent,
            repository=repo,
            repository_id=repo_name
        )
        
        print(f"⏳ Creating Artifact Registry repository {repo_name}. This may take a moment...")
        result = operation.result()
        print(f"✅ Artifact Registry repository {repo_name} created successfully in {region}.")
        return result
    except Exception as e:
        print(f"❌ Failed to create Artifact Registry repository {repo_name}. Error details: {e}")
        return None

def trigger_cloud_build(project_id: str, region: str, bucket_name: str, source_blob_name: str, repo_name: str):
    """
    Trigger a Cloud Build job from a zipped source in Google Cloud Storage.
    
    Args:
        project_id (str): Google Cloud Project ID
        region (str): GCP region for the build
        bucket_name (str): Name of the storage bucket containing the source
        source_blob_name (str): Name of the source zip blob in the bucket
        repo_name (str): Name of the Artifact Registry repository
    
    Returns:
        Build: The created Cloud Build job
    """
    # Initialize Cloud Build client
    build_client = cloudbuild_v1.services.cloud_build.CloudBuildClient()
    storage_client = storage.Client()
    
    # Prepare storage source
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    
    storage_source = StorageSource(
        bucket=bucket_name,
        object_=source_blob_name
    )
    
    source = Source(storage_source=storage_source)
    
    # Prepare build steps
    build_steps = [
        BuildStep(
            name='golang:1.23',
            args=['go', 'mod', 'download'],
            dir='/workspace'
        ),
        BuildStep(
            name='golang:1.23',
            args=['go', 'build', '-v', '-o', 'server'],
            dir='/workspace'
        ),
        BuildStep(
            name='gcr.io/cloud-builders/docker',
            args=[
                'build', 
                '-t', 
                f'{region}-docker.pkg.dev/{project_id}/{repo_name}/myapp:latest', 
                '.'
            ]
        ),
        BuildStep(
            name='gcr.io/cloud-builders/docker',
            args=[
                'push', 
                f'{region}-docker.pkg.dev/{project_id}/{repo_name}/myapp:latest'
            ]
        )
    ]
    
    # Prepare build configuration
    build = Build(
        source=source,
        steps=build_steps,
        images=[f'{region}-docker.pkg.dev/{project_id}/{repo_name}/myapp:latest']
    )
    
    # Create build
    try:
        print(f"🚀 Initiating Cloud Build for source {source_blob_name} in {region}...")
        # Use the project_id directly without the 'projects/' prefix
        operation = build_client.create_build(
            request={
                'project_id': project_id, 
                'build': build
            }
        )
        
        print(f"⏳ Cloud Build job started. Waiting for completion...")
        result = operation.result()
        
        print(f"✅ Cloud Build job completed successfully. Build ID: {result.id}")
        print(f"📦 Image built: {result.images[0]}")
        return result
    except Exception as e:
        print(f"❌ Error triggering Cloud Build: {e}")
        return None

def main():
    # Validate required environment variables
    project_id = os.environ.get('GCP_PROJECT_ID')
    if not project_id:
        print("Error: GCP_PROJECT_ID environment variable is not set.")
        print("Please set it using: export GCP_PROJECT_ID=your-project-id")
        return
    
    # Example usage - replace with your actual values
    region = 'us-central1'
    service_name = 'my-cloud-run-service'
       
    # Create Storage Bucket if it doesn't exist
    bucket_name = f"{project_id}-source-bucket"
    bucket = None
    if not check_storage_bucket_exists(project_id, bucket_name):
        bucket = create_storage_bucket(project_id, bucket_name)
    else:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.get_bucket(bucket_name)
    
    # Zip sources folder and upload to bucket
    if bucket:
        sources_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sources')
        zip_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'source.zip')
        zip_local_folder(sources_folder, zip_file_path)
        upload_to_storage_bucket(bucket, zip_file_path, 'source.zip')
    
    # Create Artifact Registry Repository if it doesn't exist
    repo_name = 'containers'
    if not check_artifact_registry_repo_exists(project_id, region, repo_name):
        create_artifact_registry_repo(project_id, region, repo_name)
    
    # Trigger Cloud Build from zipped sources
    trigger_cloud_build(project_id, region, bucket_name, 'source.zip', repo_name)
    
    # Use the newly built image for deployment
    image_url = f'{region}-docker.pkg.dev/{project_id}/{repo_name}/myapp:latest'
    
    deploy_to_cloud_run(
        project_id=project_id,
        region=region,
        service_name=service_name,
        image_url=image_url
    )

if __name__ == '__main__':
    main()
