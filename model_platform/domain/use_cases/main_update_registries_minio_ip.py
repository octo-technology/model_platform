from front.dot_env import DotEnv
from model_platform.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter

if __name__ == "__main__":
    DotEnv()
    clust = K8SDeploymentClusterAdapter()
    clust.update_mlflow_s3_ip()
