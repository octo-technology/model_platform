# Model Card for Random Forest Classifier (Iris Dataset)

## Model Details

**Name**: RandomForestClassifier (Iris)
**Version**: 1.0
**Author**: [Your Name or Organization]
**Date**: [YYYY-MM-DD]
**License**: [License Type]
**Model Type**: Supervised Classification (Random Forest)
**Frameworks**: MLflow, Scikit-learn

## Overview

This model is a **Random Forest Classifier** trained on the **Iris dataset**. It is designed to classify iris flowers
into three species (**Setosa, Versicolor, Virginica**) based on four input features.

## Intended Use

**Primary Use Case**:

- Classifying iris flower species based on input measurements.
- Educational purposes in machine learning and classification problems.
- Benchmarking Random Forest performance on structured data.

**Users**:

- Data scientists and ML engineers.
- Students learning machine learning concepts.
- Researchers experimenting with ensemble models.

## Inputs and Outputs

### Inputs

The model expects a dictionary or Pandas DataFrame with the following numerical features:

- **sepal_length** (float): Sepal length in cm.
- **sepal_width** (float): Sepal width in cm.
- **petal_length** (float): Petal length in cm.
- **petal_width** (float): Petal width in cm.

### Outputs

The model returns a dictionary containing:

- **predicted_class** (str): Predicted species label (**Setosa, Versicolor, or Virginica**).
- **class_probabilities** (dict): Probability distribution over the three classes.

## Ethical Considerations

- The model is trained on a balanced dataset and does not involve sensitive attributes.
- Predictions are based solely on input features and should not be used in unintended decision-making processes.
- Users should be aware of potential biases due to dataset limitations.

## Performance and Limitations

**Performance**:

- Evaluated on the Iris dataset with **high accuracy (>95%)**.
- Uses ensemble learning for robustness and generalization.

**Limitations**:

- Model is trained on a small, structured dataset and may not generalize well to out-of-distribution samples.
- Not suitable for tasks beyond **iris species classification**.
- Sensitive to input feature scaling and data preprocessing.

## Deployment & MLflow Integration

This model is packaged as an MLflow **pyfunc** model. It can be logged and loaded in MLflow as follows:

```python
import mlflow.pyfunc
model = mlflow.pyfunc.load_model("models:/RandomForest_Iris/1")
inputs = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
result = model.predict(inputs)
print(result)
```

## Compliance with AI Act

**Risk Category**: Low-risk classification model under AI Act classifications.
**Explainability**: The model provides feature-based decision-making, and feature importance can be extracted.
**Auditability**: Predictions and input-output mappings can be logged in MLflow.
**Fairness & Bias**: No personal data used; model trained on a well-balanced dataset.
**Safety & Robustness**: Model tested on standard dataset with strong performance metrics.

## Versioning & Updates

Future updates may include:

- Hyperparameter tuning for improved accuracy.
- Testing on additional flower classification datasets.
- Model interpretability enhancements using SHAP or feature importance visualization.

## Contact & Support

For questions or issues, contact [Your Contact Info].
