from backend.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter
from frontend.dot_env import DotEnv

if __name__ == "__main__":
    DotEnv()
    clust = K8SDeploymentClusterAdapter()
    clust.update_mlflow_s3_ip()
