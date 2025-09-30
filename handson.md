# Demi journée MLOps x SmartIndus 
30/09/2025

## Objectifs

- Se familiariser avec VIO et la model platform
- Modifier le déploiement d'un modèle sur la modèle platform pour 
  - qu'il puisse recevoir une image en input
  - retourne les prédictions au format attendu par VIO


## Prérequis
- Avoir un compte GitHub avec votre adresse Octo
- Avoir Docker installé sur votre poste
- Avoir un IDE (VSCode, PyCharm, ...)
- Installations nécessaires :
  - Docker/Colima
  - Minikube
  - Kubectl
  - Helm
  - Make
  - Python >= 3.11 
  - Poetry

Repo model platform :
https://github.com/octo-technology/model_platform/tree/vio_x_mlops_stil

Repo VIO :
https://github.com/octo-technology/VIO


## Installation de la Model Platform

Suivre les instructions du README du repo model_platform : [README.md](README.md)

## Installation de VIO

Suivre les instructions du README du repo VIO 


## Configurer l'environnement de développement python / notebook
- Créer un environnement virtuel python
    
        pip install poetry
        poetry env use 3.11.X (la version de votre python)
        poetry install --with notebooks

## Tester l'enregistrement d'un modèle et le déploiement sur la model platform

- Créer un projet dans la model platform
- Récupérer l'url du registre mlflow
- Suivre le notebook [Random Forest classifier](demos/notebooks/Random%20Forest%20classifier)
  - Changer la tracking uri mlflow par l'url du registre mlflow de votre projet
- Exécuter le notebook
- Vérifier que le modèle est bien enregistré dans la model platform
- Lancer le déploiement du modèle
- Vérifier que le modèle est bien déployé
- Récupérer l'url du modèle déployé
- Faire un post de prédiction avec le fichier [random_forest_predict.http](demos/notebooks/Random%20Forest%20classifier/random_forest_predict.http)

## Adapter la model platform pour qu'elle puisse servir un modèle de classification d'images

- Dans le dossier , [tensorflow](demos/notebooks/tensorflow) :
  - [images](demos/notebooks/tensorflow/images) images de test
  - [marker_quality_control](demos/notebooks/tensorflow/marker_quality_control) modèle pré entrainé
    - Utilisez le concept de model as code https://mlflow.org/docs/3.0.1/model/models-from-code/ pour encapsuler le modèle tensorflow
      - Encapsuler le modèle dans une classe héritant de mlflow.pyfunc.PythonModel 
        - Doit implémenter les méthodes `load_context` et `predict`
      - Logguer le modèle sur la modèle platform en utilisant la cellule 6 du notebook.
      - Déployer le modèle
      - Comprendre comment un modèle est déployer (trouver le code)
      - Faire un curl sur l'endpoint déployé avec une image
        ```
        curl -X POST http://model-platform.com/deploy/test/test-marker-quality-control-1-deployment-3b4041/predict \-F "file=@images/10.jpg"
        ```
        
### Adapter VIO pour qu'il puisse utiliser le modèle déployé sur la model paltform
 - Comprendre le fonctionne de VIO (comment changer le endpoint du model serving)
 - Il va falloir adapter la construction de l'url dans l'orchestrator VIO
 - Attention, docker doit pouvoir accéder au réseau de l'host pour pouvoir accéder à la model platform
 - La model platform tourne sur K8S, derrière un ingress et un proxy nginx...
 - Voici un début de solution
````
curl -H "Host: model-platform.com" http://host.docker.internal/deploy/test/test-marker-quality-control-1-deployment-3b4041/health
````
 