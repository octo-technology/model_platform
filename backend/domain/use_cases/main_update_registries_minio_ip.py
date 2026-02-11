from backend.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter

if __name__ == "__main__":
    clust = K8SDeploymentClusterAdapter()
    clust.update_mlflow_s3_ip()
