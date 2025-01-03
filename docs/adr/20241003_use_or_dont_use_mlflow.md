# ADR TEMPLATE

- 📅 Date: 2024/10/03
- 👷 Decision taken by: STILL, TOUL

# Context
- We are building a model platform with a key feature that is a model registry.
- MLflow is a well-known tool that offer a model registry
- After some research, it is not possible to use mlflow as a model registry only. Each model needs to be linked to an experiment-run
# Considered options 💡

1. Option 1: Use MLFlow as a registry
    - **More details:**
      - The model would be pushed from the datascientist machine to the platform using the mflow python API.
      - In order to do this, we need a running mlflow tracking server. Let's image we have an instance of mlflow tracking server running
      in a pod in a namespace (one per project) of a kubernetes cluster.
      MLflow tracking server needs :
        - **An artifact store** : we could have an S3 used as artifact store for all the projects. Or any persistent and backuped storage.
        In my opinion **the artifact store is not a problem.**
        - **A backend store** (to store the mlflow metadatas). This can only be a Database or a local folder:
        - **Database** : this means that we need to have an instance of the database running somewhere, implying managing and supporting an
        additional server (backups etc...). **Currently, we don't know if we can have multiple mlflow tracking servers using the same database.**
        - **Local folder storage** aka "mlruns". This means we need to mount a persistent storage on the k8s server running
        the mlflow tracking server.

    - ✅ **Advantage:**
      - MLflow client api for registering an artifact with the pyfunc pattern (no problems for unpickling custom objects)
      - We can expect MLFlow to move in a coherent direction with markets need, hance take advantage of all new features
    - 🚫 **Disadvantage:**
      - MLflow runs/experiments needing the backend store (database or local folder)
2. Option 2: Develop a custom solution allowing to push/list/update models in the registry.
   - **More details:**
   - ✅ **Advantage:**
     - Don't pull unneeded MLflow features, especially the runs/experiments part.
     - Metadata managed on s3 (not convinced it's optimal for r/w)

   - 🚫 **Disadvantage:**
     - Pickling custom inference pipelines is complicated as the definition of the custom object would have to be packaged with the pickle in order to be unpickled correctly.
     - Receiving large objects (artifacts) via an API is complicated
     - All dependencies must be specified manually by the user pushing the model.



# Advices
<--Any advices worth mentioning-->

# Decision 🏆
<--Which decision have been taken and what was the decider-->

# Consequences
<-- Consequences of your decision -->

♻️ Update: <date>.
