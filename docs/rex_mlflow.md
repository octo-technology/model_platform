# Exploration with MLFlow
Author : TOUL, BACO

### Context

We are building a model plateforme that would offer the following capabilities

- Model registry
- Model deployment
- Model runners

We expect it to be cloud provider-agnostic, or even run on premise.

MLflow seems to be a good candidate.

## Registry

MLflow registry, is a well-known registry for models.

The way it works mainly is the following:

1. Make a training
2. Register experimentation, metrics and log model
    ```python
    import mlflow
    model = ...
    with mlflow.start_run() as run:
        mlflow.sklearn.log_model(model, "model")
    ```
3. Register model to registry
    ```python
   mlflow.register_model(f"runs:/{run.info.run_id}/model", "model")
   ```

This requires to be coupled with tracking, our idea so far is to be independent of training.

It can be done all at once

```python
mlflow.sklearn.log_model(
    sk_model=model,
    artifact_path="sklearn-model",
    signature=infer_signature(model_inputs=df),
    registered_model_name="sk-learn-random-forest-reg-model",
)
```

What we like:
- Mlflow will identify the requirements and store them directly
  - Counter-argument: auto-identified dependencies can become tricky, and mlflow even offer an api to update dependencies.
  - NB: dependencies will need to be checked for security issues (using `safety` for example)
- Method `infer_signature` allow to generate a json that describe expected input
What we dislike:
- Didn't identify a method to go straight to model registry without logging an experiment

## Build a runer
### Mlflow serve

To serve a model with mlflow:
```shell
mlflow models serve -m models:/model/1 --env-manager=local
```

This will retrieve the model and provide an api.

What we like:
- An api generated with 1 command
- Can generate a dedicated conda env

What we don't like
- It doesn't offer a swagger, that we could have with a fastapi
- It doesn't offer (yet ?) advanced feature such as A/B testing, shadow production, ...

### Mlflow generate-dockerfile

```shell
 mlflow models generate-dockerfile -m models:/model/1
```
Will generate:
```
| mlflow-dockerfile
└───model_dir
│      conda.yml
│      model.pkl
│      ...
│   Dockerfile
```
So it created a copy of the model registry in folder `model_dir` and a Dockerfile that is based on mlflow serve. It is a 1.19GB image.

Image build is require every time models change.

Image is about the size of a python-slim.

What we like:
- A Dockerfile in one command line

What we don't like
- Dockerfile is a bit ugly
