# Philippe Stepniewski
import typer

from cli.utils.api_calls import get_and_print
from cli.utils.token import get_client


def submit_batch(
    project_name: str,
    model_name: str,
    version: str,
    file_path: str = typer.Option(..., help="Path to the CSV file to process"),
):
    """Submit a batch prediction job"""
    client = get_client()
    with open(file_path, "rb") as f:
        r = client.post(
            f"/{project_name}/batch/submit/{model_name}/{version}",
            files={"file": (file_path.split("/")[-1], f, "text/csv")},
        )
    if r.status_code == 200:
        result = r.json()
        print(f"Batch job submitted successfully. Job ID: {result.get('job_id', 'unknown')}")
    else:
        print(f"Error submitting batch job: {r.text}")


def batch_status(project_name: str, job_id: str):
    """Get the status of a batch prediction job"""
    get_and_print(
        f"/{project_name}/batch/status/{job_id}",
        error_message="Error fetching batch job status",
        success_message="Batch job status retrieved",
    )


def list_batch_jobs(project_name: str):
    """List all batch prediction jobs for a project"""
    get_and_print(
        f"/{project_name}/batch/list",
        error_message="Error listing batch jobs",
        success_message="No batch jobs found",
    )


def download_batch_result(
    project_name: str,
    job_id: str,
    output: str = typer.Option("predictions.csv", help="Output file path"),
):
    """Download the result of a batch prediction job"""
    client = get_client()
    r = client.get(f"/{project_name}/batch/download/{job_id}")
    if r.status_code == 200:
        with open(output, "wb") as f:
            f.write(r.content)
        print(f"Results downloaded to {output}")
    else:
        print(f"Error downloading batch result: {r.text}")


def delete_batch_job(project_name: str, job_id: str):
    """Delete a batch prediction job and its files"""
    client = get_client()
    r = client.delete(f"/{project_name}/batch/{job_id}")
    if r.status_code == 200:
        print("Batch job deleted successfully")
    else:
        print(f"Error deleting batch job: {r.text}")
