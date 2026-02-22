import marimo

__generated_with = "0.20.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Jusqu'à maintenant, nous avons vu avec MLflow la puissance du composant Tracking, qui permettait de fournir un historique des expérimentations réalisées en gardant une tracabilité des hyper-paramètres utilisés, des métriques obtenus mais également des artifacts générés (modèle, graphique).

    Il y a également un autre composant particulièrement utile en tant que ML Engineer : c'est le **registre de modèle**. À l'instar d'un dépôt Git, le registre de modèle MLflow permettra de gérer plusieurs versions de modèles en leur attribuant également des tags, qui correspondent à des environnement de pré-production (*staging*) et de production.

    <blockquote><p>🙋 <b>Ce que nous allons faire</b></p>
    <ul>
        <li>Intégrer le tracking MLflow dans Kedro</li>
        <li>Créer un modèle packagé sous MLflow</li>
        <li>Versioner les modèles dans Kedro</li>
    </ul>
    </blockquote>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tracking MLflow sous Kedro

    Dans le Notebook MLflow, nous avions entraîné un LightGBM manuellement et l'avons envoyé directement sur MLflow et Cloud Storage. L'objectif ici est de modifier le pipeline `training` sous Kedro pour y ajouter l'intégration avec MLflow.

    Commençons par ajouter une variable d'environnement. Sous Python, le package `python-dotenv` est utile pour récupérer les variables d'environnement ou pour en configurer automatiquement lors du développement du projet.
    """)
    return


app._unparsable_cell(
    r"""
    uv add python-dotenv mlflow google-cloud-storage
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    À la racine du projet, créons le fichier `.env`.
    """)
    return


app._unparsable_cell(
    r"""
    # Remplacer par l'adresse IP de la VM contenant MLflow
    MLFLOW_SERVER=http://XX.XX.XX.XX/
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Le rôle de ce fichier est identique à un `export` qui serait réalisé sur chaque variable. Le principal intérêt, en plus de pouvoir centraliser toutes les variables d'environnement, est que `python-dotenv` supporte aussi les variables d'environnement : il peut donc être utilisé à la fois lors du développement ou une fois le code en production.

    À noter que nous aurions pu utiliser le fichier `parameters.yml` de Kedro. Dans la pratique, ce fichier est plutôt réservé aux paramètres des pipelines (ratio pour l'ensemble de test, hyper-paramètres par défaut, etc), et il est préférable, comme c'est le cas en développement logiciel, d'inscrire des paramètres plus généraux (comme les références aux servers, l'environnement de pré-production ou de production) dans des fichiers de configuration ou des variables d'environnement.

    Ouvrons le fichier `__init__.py` dans le dossier `training` des pipelines.
    """)
    return


@app.cell
def _():
    """
    This is a boilerplate pipeline 'training'
    generated using Kedro 1.2.0
    """

    from dotenv import load_dotenv

    from .pipeline import create_pipeline

    load_dotenv()
    __all__ = ["create_pipeline"]

    __version__ = "0.1"
    return (load_dotenv,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Pour rappel, ce fichier sera exécuté initialement par l'interpréteur Python, permettant ainsi de définir des configurations qui seront partagées par tous les fichiers du module/dossier. Par la suite, nous allons pouvoir appeler `os.getenv("MLFLOW_SERVER")` pour récupérer cette variable d'environnement dans n'importe quel fichier du dossier contenant ce `__init__.py`.

    Nous allons ajouter deux paramètres dans `parameters.yml`.
    """)
    return


@app.cell
def _():
    mlflow_enabled: True # Do we log metrics and artifacts to MLflow ?
    mlflow_experiment_id: 1 # Experimented ID associated to this project
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Cela permet de décider à tout moment si l'on souhaite envoyer les logs et artifacts vers MLflow, ainsi que l'identifiant de l'expérience MLflow.

    Dans `nodes.py` de `training`, modifiant la fonction `auto_ml` pour accepter ces deux nouveaux paramètres.
    """)
    return


app._unparsable_cell(
    r"""
    def auto_ml(
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        max_evals: int = 40,
        log_to_mlflow: bool = False,
        experiment_id: int = -1,
    ) -> dict[str, BaseEstimator]:
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Par défaut, si aucune information n'est spécifiée concernant MLflow, on préfère ne pas envoyer de logs ou d'artifacts. Importons `os` ainsi que `mlflow`.
    """)
    return


@app.cell
def _():
    import os
    import numpy as np
    import pandas as pd
    import mlflow

    return mlflow, np, os


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Au tout début de la fonction, après avoir récupéré la base d'apprentissage $(X, y)$, nous démarrons un run.
    """)
    return


app._unparsable_cell(
    r"""
    X = pd.concat([pd.DataFrame(X_train), pd.DataFrame(X_test)], ignore_index=True)

    y = pd.concat((y_train, y_test))
        # Convert y to Series
        y_train_flat = y_train.squeeze() if isinstance(y_train, pd.DataFrame) else y_train
        y_test_flat = y_test.squeeze() if isinstance(y_test, pd.DataFrame) else y_test

        y = pd.concat([pd.Series(y_train_flat), pd.Series(y_test_flat)], ignore_index=True)

    run_id:str = ""
    if log_to_mlflow:
        mlflow.set_tracking_uri(os.getenv("MLFLOW_SERVER", "http://localhost:5000"))
        run: mlflow.ActiveRun = mlflow.start_run(experiment_id=str(experiment_id))
        run_id = run.info.run_id
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Si l'on souhaite tracker avec MLflow (`log_to_mlflow` à `True`), alors on spécifie l'URL de tracking, puis on lance un run avec `start_run` en indiquant l'identifiant de l'expérience associé au run.

    À la fin de la fonction, nous envoyons les logs et artifacts vers MLflow. Elle retournera également le champ `mlflow_run_id`.
    """)
    return


@app.cell
def _(BaseEstimator, np, opt_models, run_id, save_pr_curve):
    # A ajouter au dessus
    from mlflow.models import infer_signature
    import mlflow.sklearn

    # On oublie pas de changer la sigature de la fonction, qui est rappelé ici :
    def auto_ml(
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        max_evals: int = 40,
        log_to_mlflow: bool = False,
        experiment_id: int = -1,
    ) -> dict[str, BaseEstimator | str]:
    
        #
        # ... 
        #
    
        # In case we have multiple models
        best_model = max(opt_models, key=lambda x: x["score"])
    
        if log_to_mlflow:
            model_metrics = {
                "f1": best_model["score"]
            }
            signature = infer_signature(X_train, best_model["model"].predict(X_train))
            save_pr_curve(X_test, y_test, best_model["model"])
    
            mlflow.log_metrics(model_metrics)
            mlflow.log_params(best_model["params"])
            # Only use if validation curves are produced
            mlflow.log_artifacts("data/08_reporting", artifact_path="plots")
            mlflow.sklearn.log_model(best_model["model"], "model", signature=signature)
    
            mlflow.end_run()
    
        return {"model": best_model["model"], "mlflow_run_id": run_id}  # Return just the model from the best_model dict


    return auto_ml, mlflow


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Il nous reste à ajouter une nouvelle fonction pour logger les plots dans le dossier data/08_reporting
    """)
    return


@app.cell
def _(os):
    from matplotlib import pyplot as plt
    import matplotlib.ticker as mtick
    from sklearn.metrics import precision_recall_curve, PrecisionRecallDisplay

    def save_pr_curve(X, y, model):
        plt.figure(figsize=(16, 11))
        prec, recall, _ = precision_recall_curve(y, model.predict_proba(X)[:, 1], pos_label=1)
        pr_display = PrecisionRecallDisplay(precision=prec, recall=recall).plot(ax=plt.gca())
        plt.title('PR Curve', fontsize=16)
        plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter(1, 0))
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1, 0))
        plt.savefig(os.path.expanduser('data/08_reporting/pr_curve.png'))
        plt.close()

    return (save_pr_curve,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    La dernière modification à apporter est de mettre à jour la définition du pipeline.
    """)
    return


@app.cell
def _(Pipeline, auto_ml, node):
    def create_pipeline(**kwargs):
        return Pipeline(
            [
                node(
                    auto_ml,
                    [
                        "X_train", "y_train", "X_test", "y_test",
                        "params:automl_max_evals", "params:mlflow_enabled",
                        "params:mlflow_experiment_id"],
                    dict(model="model", mlflow_run_id="mlflow_run_id"),
                )
            ]
        )

    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Nous pouvons vérifier visuellement notre pipeline à l'aide de la commande suivante :

    ```
    uv run kedro viz run --port 4141
    ```
    Attention, pandas vient d'être mise à jour vers la version 3, elle n'est pas compatible avec la dernière version de MLFlow et de Protobuf utilisé par google-cloud-storage.

    Nous avons donc un problème de dépendance du projet à gérer, et pour le faire fonctionner, nous allons demander à UV des conditions de dépendance nécessaire :
    ```
    uv add "pandas>=2.0.0,<3.0.0" "mlflow>=2.10.0"
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ![alt](public/model_registry3.png)

    Avant d'exécuter le pipeline, il faut penser à donner les droits d'écriture sur Cloud Storage au compte de service de Kedro. Rappelons-nous, nous avions crée un compte de service pour pouvoir récupérer les fichiers CSV sur le bucket. Pas besoin d'en créer un nouveau : nous pouvons utiliser celui existant en lui rajoutant de nouvelles autorisations.

    Dirigeons-nous dans <a href="https://console.cloud.google.com/iam-admin/iam" target="_blank">IAM</a> et éditons le membre `purchase-predict@...`.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry1.png" />

    Ajoutons le rôle Créateur des objets de l'espace de stockage. Après modification des rôles, il faut retélécharger une clé pour <a href="https://console.cloud.google.com/iam-admin/serviceaccounts" target="_blank">le compte de service</a>. Une fois le contenu de la clé modifié dans `conf/local/service-account.json`, nous devons mettre à jour la variable d'environnement `GOOGLE_APPLICATION_CREDENTIALS`.
    """)
    return


app._unparsable_cell(
    r"""
    export GOOGLE_APPLICATION_CREDENTIALS="conf/local/service-account.json"
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    À noter que pour aller plus vite, nous pouvons définir cette variable dans le fichier `.env`.

    Temporairement, pour vérifier que notre code fonctionne, nous allons modifier le paramètre `automl_max_evals` à $1$.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Exécutons le pipeline `global`.
    """)
    return


app._unparsable_cell(
    r"""
    uv run kedro run
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Après quelques dizaines de secondes, le run devrait être visible sous MLflow.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry2.png" />

    N'oublions pas, puisque le test est concluant, de remettre `automl_max_evals` à sa valeur d'origine.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Pipeline de déploiement vers MLflow

    Pour l'instant, nous avons uniquement effectué du tracking. Bien que cela soit pratique pour historiser et garder une trace des différentes exécutions des pipelines d'entraînement, cela ne permet pas directement de gérer efficacement des **versions de modèles**.

    ### Registre de modèles

    Le **Model Registry** (registre de modèles) est un composant de MLflow qui permet de gérer des versions de modèles de Machine Learning, en proposant également des **stages** (états).

    - Le tag **staging** correspond à un modèle considéré comme pré-production.
    - Le tag **production** correspond à un modèle qui serait en environnement de production.
    - Le tag **archived** pour les anciens modèles staging ou production archivés.

    C'est un composant particulièrement utile pour gérer le cycle de vie des modèles, car le cycle staging, production et archive est couramment appliqué lorsque des modèles sont mis à jour régulièrement. Sous MLflow, l'onglet Models permet d'afficher tous les modèles enregistrés.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry4.png" />

    Retournons dans les expériences et choisissons le dernier run que nous avons lancé. En cliquant sur `model` dans les artifacts, un bouton *Register Model* apparaît à droite.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry5.png" />

    En cliquant dessus, nous allons pouvoir ajouter manuellement le modèle au registre. Pour cela, nous devons créer un nouveau modèle que l'on nommera `purchase_predict`.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry6.png" />

    En retournant dans Models, nous voyons que la version 1 (le modèle que nous venons d'ajouter est bien présent).

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry7.png" />

    En cliquant dessus, nous avons accès à plus de détails sur les différentes versions présentes.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry8.png" />

    Pour une version spécifique, nous pouvons manuellement transitionner vers un état de pré-production ou de production. L'objectif sera d'automatiser cette tâche pour automatiquement changer l'état d'un modèle que l'on aura entraîné.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry9.png" />

    ### Pipeline de déploiement

    Une fois l'entraînement réalisé, nous allons également implémenter dans Kedro un pipeline qui va permettre de transitionner l'état d'un modèle en staging ou production. Pour cela, nous allons créer un pipepline `deployment` avec les trois fichiers `__init__.py`, `nodes.py` et `pipeline.py`. Le fichier `__init__.py` contiendra les mêmes instructions.
    """)
    return


@app.cell
def _(load_dotenv):
    load_dotenv()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Nous allons créer deux fonctions dans le fichier `nodes.py`.

    - La fonction `push_to_model_registry` va envoyer un modèle enregistré dans tracking vers le registre de modèle associé. Notons que pour cela, le modèle doit déjà être dans le tracking.
    - La fonction `stage_model` qui permet de transitionner un modèle du registre vers un état staging ou production.
    """)
    return


@app.cell
def _(mlflow, os):
    from mlflow.tracking import MlflowClient

    def push_to_model_registry(registry_name: str, run_id: int):
        """
        Pushes a model's version to the specified registry.
        """
        mlflow.set_tracking_uri(os.getenv('MLFLOW_SERVER'))
        result = mlflow.register_model('runs:/{}/artifacts/model'.format(run_id), registry_name)
        return result.version

    def stage_model(registry_name: str, version: int):
        """
        Stages a model version pushed to model registry.
        """
        env = os.getenv('ENV')
        if env not in ['staging', 'production']:
            return
        client = MlflowClient()
        client.transition_model_version_stage(name=registry_name, version=int(version), stage=env[0].upper() + env[1:])

    return push_to_model_registry, stage_model


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Nous avons besoin de configurations supplémentaires, `registry_name`, pour référencer le nom du modèle dans le registre, que l'on ajoute au fichier `parameters.yml`, ainsi que la variable d'environnement `ENV` pour spécifier si le projet Kedro est exécuté dans un environnement de pré-production ou de production. Modifions le fichier `.env`.
    """)
    return


app._unparsable_cell(
    r"""
    ENV=staging
    # Remplacer par l'adresse IP de la VM contenant MLflow
    MLFLOW_SERVER=http://xx.xx.xx.xx/
    GOOGLE_APPLICATION_CREDENTIALS="conf/local/service-account.json"
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    De même pour le fichier `parameters.yml`.
    """)
    return


@app.cell
def _():
    mlflow_model_registry: "purchase_predict" # Name of model registry of this project
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Le paramètre `run_id` sera lui fourni par le catalogue de données. Écrivons le code du pipeline, qui ne présente aucune difficulté.
    """)
    return


@app.cell
def _(push_to_model_registry, stage_model):
    from kedro.pipeline import Pipeline, node

    def create_pipeline_1(**kwargs):
        return Pipeline([node(push_to_model_registry, ['params:mlflow_model_registry', 'mlflow_run_id'], 'mlflow_model_version'), node(stage_model, ['params:mlflow_model_registry', 'mlflow_model_version'], None)])

    return Pipeline, node


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Avant de passer à la suite, nous devons définir notre ml_run_id qui va récupérer le numéro du run depuis l'entrainement afin de passer l'information lors du déploiement. Il sera définit dans notre catalogue
    """)
    return


app._unparsable_cell(
    r"""
    mlflow_run_id:
      type: MemoryDataset
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Il ne reste plus qu'à renseigner ce pipeline dans `hooks.py`.
    """)
    return


@app.cell
def _(
    Dict,
    Pipeline,
    hook_impl,
    loading_pipeline,
    processing_pipeline,
    training_pipeline,
):
    from purchase_predict.pipelines.deployment import pipeline as deployment_pipeline

    class ProjectHooks_1:

        @hook_impl
        def register_pipelines(self) -> Dict[str, Pipeline]:
            """Register the project's pipeline.

            Returns:
                A mapping from a pipeline name to a ``Pipeline`` object.

            """
            p_processing = processing_pipeline.create_pipeline()
            p_training = training_pipeline.create_pipeline()
            p_loading = loading_pipeline.create_pipeline()
            p_deployment = deployment_pipeline.create_pipeline()
            return {'global': Pipeline([p_loading, p_processing, p_training, p_deployment]), 'loading': p_loading, 'processing': p_processing, 'training': p_training, 'deployment': p_deployment}

    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Nous obtenons le pipeline suivant.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry10.png" />

    Lançons une exécution globale (en spécifiant là-aussi le paramètre `automl_max_evals` à 1 pour accélerer les calculs.
    """)
    return


app._unparsable_cell(
    r"""
    kedro run --pipeline global
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Puisque nous sommes en environnement staging, sur MLflow, le modèle enregistré doit avoir l'état correspondant.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry12.png" />

    Nous avons donc à la fois la *Latest Version* à 2, et c'est elle qui est actuellement en staging.

    L'intégralité des pipelines ont été réalisées, ce qui donne pour le pipeline `global` un ensemble assez important d'étapes.

    <img src="https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/training/ml_engineer_facebook/img/model_registry11.png" />

    > ❓ En quoi envoyer le modèle vers le registre peut nous être utile ?

    Ce qui va être puissant, c'est que l'on sera capable de récupérer, dans un projet différent que Kedro, le modèle le plus à jour. Ainsi, on **découple fortement** la phase d'expérimentation/d'entraînement du modèle et la phase de déploiement, qui est une bonne pratique du Cloud.

    Comme toujours, il ne faut pas hésiter à régulièrement pousser son code vers le dépôt Git.
    """)
    return


app._unparsable_cell(
    r"""
    git add .
    git commit -am "Integrated all pipelines"
    """,
    name="_"
)


app._unparsable_cell(
    r"""
    black....................................................................Passed
    flake8...................................................................Passed
    [master 31d0824] Integrated all pipelines
     20 files changed, 549 insertions(+), 16 deletions(-)
     create mode 100644 src/purchase_predict/pipelines/deployment/__init__.py
     create mode 100644 src/purchase_predict/pipelines/deployment/nodes.py
     create mode 100644 src/purchase_predict/pipelines/deployment/pipeline.py
     create mode 100644 src/purchase_predict/pipelines/training/__init__.py
     create mode 100644 src/requirements.in
     create mode 100644 src/tests/pipelines/loading/__init__.py
     create mode 100644 src/tests/pipelines/loading/conftest.py
     create mode 100644 src/tests/pipelines/loading/test_nodes.py
     create mode 100644 src/tests/pipelines/loading/test_pipeline.py
     create mode 100644 src/tests/pipelines/processing/__init__.py
     create mode 100644 src/tests/pipelines/processing/conftest.py
     create mode 100644 src/tests/pipelines/processing/test_nodes.py
     create mode 100644 src/tests/pipelines/processing/test_pipeline.py
    (venv) jovyan@jupyter-604a3b76-2d8f51-2d448a-2d8a79-2d0bb4e5cd11e4:~/purchase_predict$ git status
    On branch master
    nothing to commit, working tree clean
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Nous allons créer une **nouvelle branche** appelée staging. Cela va nous permettre de produire un code en environnement de pré-production.
    """)
    return


app._unparsable_cell(
    r"""
    git checkout -b staging
    git commit -am "New staging branch"
    git push google staging
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    On n'oubliera pas d'ajouter la clé SSH à l'agent avec de pousser vers le dépôt.
    """)
    return


app._unparsable_cell(
    r"""
    ssh-add ~/ssh/git_key
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Sur <a href="https://source.cloud.google.com/" target="_blank">Cloud Source</a>, la branche `staging` est désormais visible.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ✔️ Conclusion

    Dorénavant, le projet Kedro peut exécuter le pipeline ML de A à Z avec MLflow pour centraliser les différents modèles qui seront entraînés.

    - Nous avons intégré le tracking MLflow sous Kedro.
    - Nous avons créer un modèle packagé sous MLflow.
    - Nous sommes capable de changer les états des modèles de pré-production et de production automatiquement.

    > ➡️ Nous avons un modèle prêt à être utilisé. Mais pour être utilisé, il faut le rendre accessible ... et la meilleure manière de le faire, c'est de <b>construire une API</b>.
    """)
    return


if __name__ == "__main__":
    app.run()
