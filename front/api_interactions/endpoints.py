import os

from front.dot_env import DotEnv

DotEnv()
## API
API_BASE_URL = "http://0.0.0.0:8001"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

## PROJECT ROUTES
PROJECT_LIST_ENDPOINT = f"{API_BASE_URL}/projects/list"
PROJECT_INFO_URL = API_BASE_URL + "/projects/{PROJECT_NAME}/info"
ADD_PROJECT_URI = API_BASE_URL + "/projects/add"
PROJECT_GOVERNANCE = API_BASE_URL + "/projects/{project_name}/governance".format(project_name="{project_name}")

## MODEL ROUTES
MODELS_LIST_ENDPOINT = "{API_BASE_URL}/{project_name}/models/list".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}"
)
MODEL_VERSION_ENDPOINT = "{API_BASE_URL}/{project_name}/models/{model_name}/versions".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}", model_name="{model_name}"
)

## DEPLOYMENT ROUTES
# GET http://0.0.0.0:8001/test/models/deploy/test_model/1
DEPLOY_MODEL_ENDPOINT = "{API_BASE_URL}/{project_name}/models/deploy/{model_name}/{model_version}".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}", model_name="{model_name}", model_version="{model_version}"
)

# build status endpoint http://0.0.0.0:8001/test/models/task-status/
BUILD_DEPLOY_STATUS_ENDPOINT = "{API_BASE_URL}/{project_name}/models/task-status/{task_id}".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}", task_id="{task_id}"
)

# GET http://0.0.0.0:8001/test/models/undeploy/test_model/1
UNDEPLOY_MODEL_ENDPOINT = "{API_BASE_URL}/{project_name}/models/undeploy/{model_name}/{model_version}".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}", model_name="{model_name}", model_version="{model_version}"
)

## DEPLOYED ROUTES
# GET http://0.0.0.0:8001/test/deployed_models/list
DEPLOYED_MODELS_LIST_ENDPOINT = "{API_BASE_URL}/{project_name}/deployed_models/list".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}"
)

REMOVE_DEPLOYMENT_FROM_DB_ENDPOINT = (
    "{API_BASE_URL}/{project_name}/deployed_models/remove/{model_name}/{model_version}".format(
        API_BASE_URL=API_BASE_URL,
        project_name="{project_name}",
        model_name="{model_name}",
        model_version="{model_version}",
    )
)

## DEPLOYED MODEL URI
DEPLOYED_MODEL_URI = "http://{MP_HOST_NAME}/deploy/{project_name}/{deployment_name}".format(
    MP_HOST_NAME=os.environ["MP_HOST_NAME"], project_name="{project_name}", deployment_name="{deployment_name}"
)

### AUTH
AUTH_URI = f"{API_BASE_URL}/auth/token"
