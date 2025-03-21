# Model Card for PyTorch Classifier (FashionMNIST)

## Model Details

**Name**: FashionMNIST_PyTorch_Classifier
**Version**: 1.0
**Author**: [Your Name or Organization]
**Date**: [YYYY-MM-DD]
**License**: [License Type]
**Model Type**: Supervised Classification (Convolutional Neural Network)
**Frameworks**: PyTorch, MLflow

## Overview

This model is a **Convolutional Neural Network (CNN)** trained on the **FashionMNIST dataset**. It classifies grayscale
images of clothing items into 10 categories.

## Intended Use

**Primary Use Case**:

- Image classification of fashion items into predefined categories.
- Educational purposes in deep learning and CNN architectures.
- Benchmarking PyTorch models on vision tasks.

**Users**:

- Data scientists and ML engineers.
- Students learning deep learning with PyTorch.
- Researchers experimenting with CNNs and transfer learning.

## Inputs and Outputs

### Inputs

The model expects a **28x28 grayscale image** as a NumPy array or PyTorch tensor.

### Outputs

The model returns a dictionary containing:

- **predicted_class** (str): Predicted clothing category.
- **class_probabilities** (dict): Probability distribution over the 10 categories.

## Ethical Considerations

- The model does not involve sensitive personal data.
- Predictions are based on pixel values and should not be used in high-stakes decision-making.
- Users should ensure the dataset and predictions align with their specific use case.

## Performance and Limitations

**Performance**:

- Evaluated on FashionMNIST test set with **high accuracy (>90%)**.
- Uses CNNs for robust feature extraction.

**Limitations**:

- Model trained only on grayscale 28x28 images; performance may drop on real-world images.
- Not designed for general fashion item recognition outside FashionMNIST categories.

## Deployment & MLflow Integration

This model is packaged as an MLflow **pyfunc** model. It can be logged and loaded in MLflow as follows:

```python
import mlflow.pyfunc
torch_model = mlflow.pyfunc.load_model("models:/FashionMNIST_PyTorch/1")
import torch
sample_image = torch.rand(1, 1, 28, 28)  # Random example input
result = torch_model.predict(sample_image)
print(result)
```

## Compliance with AI Act

**Risk Category**: Low-risk classification model under AI Act classifications.
**Explainability**: CNN feature maps and activations can be analyzed.
**Auditability**: Model predictions can be logged in MLflow for traceability.
**Fairness & Bias**: No personal data used; dataset represents a variety of clothing items.
**Safety & Robustness**: Model tested on standard dataset with strong performance.

## Versioning & Updates

Future updates may include:

- Transfer learning with larger fashion datasets.
- Model interpretability improvements with Grad-CAM.
- Enhanced data augmentation techniques for robustness.

## Contact & Support

For questions or issues, contact [Your Contact Info].
