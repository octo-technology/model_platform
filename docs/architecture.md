Two options are beeing considered for the architecture of our model platform:
## Option 1: MLflow

The model would be pushed from the datascientist machine to the platform using the mflow python API. 

In order to do this, we need a running mlflow tracking server. Let's image we have an instance of mlflow tracking server running 
in a pod in a namespace (one per project) of a kubernetes cluster.

MLflow tracking server needs : 
- **An artifact store** : we could have an S3 used as artifact store for all the projects. Or any persistent and backuped storage. 
In my opinion **the artifact store is not a problem.** 
- **A backend store** (to store the mlflow metadatas). This can only be a Database or a local folder:
  - **Database** : this means that we need to have an instance of the database running somewhere, implying managing and supporting an
additional server (backups etc...).
  - **Local folder storage** aka "mlruns". This means we need to mount a persistent storage on the k8s server running
the mlflow tracking server. 

**Pros:**
- MLflow client api for registering an artifact with the pyfunc pattern (no problems for unpickling custom objects)

**Cons:**
- MLflow runs/experiments needing the backend store (database or local folder)

## Option 2: NO MLflow

MLflow comes with a lot of features that we don't need, especially the runs/experiments part. **After some research,
it is not possible to use mlflow as an model registry only. Each model needs to be linked to a run**

An option would be to create our **own model registry with a rest API allowing to push/list/update models in the registry.**

**Pros:**
- No mlflow? 
- Metadata managed on s3 (not convinced it's optimal for r/w)

**Cons:**
- Pickling custom inference pipelines is complicated as the definition of the custom object would have to be packaged with the
pickle in order to be unpickled correctly.
- Receiving large objects (artifacts) via an API is complicated
- All dependencies must be specified manually by the user pushing the model. 





