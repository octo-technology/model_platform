## Définitions
- VERSION -> Est un artefact avec ses metadata
- PROJET -> problématique métier
- MODEL -> Un modèle, infère la même chose, quand on met un modèle il remplace en théorie le modèle précédent. (au moins en partie si on fait de l'AB testing). Par exemple un nouveau modèle pour la même raffinerie.
- DEPLOIEMENT -> Appliquer une recette de déploiement (configuration) / Declencher des workers qui exécutent un ou plusieurs modèles
- ENVIRONNEMENT -> Ensemble des ressources nécessaires pour déployer un modèle (runner, ressources, etc)
  - Par exemple: dans un repo, on peut avoir la v1 qui est une reglog, et la v2 qui est un xgboost

## Etapes :
- Un Projet a été créé
- Les droits d'accès au projet ont été configurés
- Un nouvel utilisateur a été créé
- Un modèle a été créé
- Une version a été poussée.
- L'artefact de la version a été sauvegardé avec ses metadata
- Une version a été tagguée
- Le deploy d'une version a été demandée
- Une recette de déploiement a été configurée
- Un environnement de run a été créé/modifié (un endpoint a été exposé) => Q : Comment on gère la continuité de service en changeant de version ?
- Des prédictions ont été demandées
- L'environnement s'est adapté à la charge
- Une inférence a été logguée
- Les métriques et logs ont été consultés => Q : Quid du suivi de la performance / du drift pendant le run ?
- Un modèle a été décommissionné

## Etapes parking
- La liste des modèles a été consultée.
## Etapes gouvernance
- La liste des version a été consulté.
## Etapes sécurité
- Les droits d'accès au endpoint ont été configurés
- L'accès à l'API a été sécurisé