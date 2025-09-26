import os

from frontend.dot_env import DotEnv

DotEnv()
## API
API_BASE_URL = "http://backend.model-platform.svc.cluster.local:8000"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
ARTIFACTS_ENDPOINT = os.environ['MLFLOW_S3_ENDPOINT_URL']

## PROJECT ROUTES
PROJECT_LIST_ENDPOINT = f"{API_BASE_URL}/projects/list"
PROJECT_INFO_URL = API_BASE_URL + "/projects/{PROJECT_NAME}/info"
ADD_PROJECT_URI = API_BASE_URL + "/projects/add"
PROJECT_GOVERNANCE = API_BASE_URL + "/projects/{project_name}/governance".format(project_name="{project_name}")
DELETE_PROJECT = API_BASE_URL + "/projects/{project_name}/remove".format(project_name="{project_name}")
DOWNLOAD_GOVERNANCE = API_BASE_URL + "/projects/{project_name}/download_governance".format(
    project_name="{project_name}"
)

## MODEL ROUTES
MODELS_LIST_ENDPOINT = "{API_BASE_URL}/{project_name}/models/list".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}"
)
MODEL_VERSION_ENDPOINT = "{API_BASE_URL}/{project_name}/models/{model_name}/versions".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}", model_name="{model_name}"
)
SEARCH_HUGGING_FACE = "{API_BASE_URL}/hugging_face/search?search_args={SEARCH_ARGS}".format(
    API_BASE_URL=API_BASE_URL, SEARCH_ARGS="{SEARCH_ARGS}"
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

GET_HF_MODEL_ENDPOINT = "{API_BASE_URL}/hugging_face/get_model/?project_name={project_name}&model_id={model_id}".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}", model_id="{model_id}"
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
CREATE_USER_URI = "{API_BASE_URL}/users/add?email={email}&password={password}&role=SIMPLE_USER".format(
    API_BASE_URL=API_BASE_URL, email="{email}", password="{password}"
)
GET_ALL_USERS_URI = "{API_BASE_URL}/users/get_all".format(API_BASE_URL=API_BASE_URL)
ADD_USER_TO_PROJECT = "{API_BASE_URL}/projects/{project_name}/add_user?email={email}&role={role}".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}", email="{email}", role="{role}"
)
GET_USERS_FOR_PROJECT = "{API_BASE_URL}/projects/{project_name}/users".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}"
)
DELETE_USER_FOR_PROJECT = "{API_BASE_URL}/projects/{project_name}/remove_user?email={email}".format(
    API_BASE_URL=API_BASE_URL, project_name="{project_name}", email="{email}"
)
CHANGE_USER_ROLE_FOR_PROJECT = (
    "{API_BASE_URL}/projects/{project_name}/change_user_role?email={email}&role={role}".format(
        API_BASE_URL=API_BASE_URL, project_name="{project_name}", email="{email}", role="{role}"
    )
)
