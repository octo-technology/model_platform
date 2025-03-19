# Model Card for OptimModel

## Model Details
**Name**: OptimModel
**Version**: 1.0
**Author**: [Your Name or Organization]
**Date**: [YYYY-MM-DD]
**License**: [License Type]
**Model Type**: Optimization Model using Linear Programming (Pywraplp)
**Frameworks**: MLflow, OR-Tools (Pywraplp)

## Overview
OptimModel is a mathematical optimization model designed to maximize profit under given constraints. It uses an integer linear programming solver to determine the optimal values of two decision variables (x1, x2) while respecting work and material constraints. The model is implemented using Google's OR-Tools library.

## Intended Use
**Primary Use Case**:
- Optimizing resource allocation based on profit and constraints.
- Decision-making for production planning.
- Educational and research purposes.

**Users**:
- Data scientists working on optimization problems.
- Business analysts optimizing resource allocation.
- Researchers in operations research and applied mathematics.

## Inputs and Outputs
### Inputs
The model expects a dictionary or Pandas DataFrame with the following parameters:
- **profit_P1** (float): Profit per unit of product 1.
- **profit_P2** (float): Profit per unit of product 2.
- **work_limit** (int): Maximum available work capacity.
- **material_limit** (int): Maximum available material capacity.

### Outputs
The model returns a dictionary containing:
- **status** (str): Solution status (optimal, infeasible, unbounded, abnormal, etc.).
- **x1** (int): Optimal number of units for product 1.
- **x2** (int): Optimal number of units for product 2.
- **profit** (float): Total profit achieved with the optimal solution.

## Ethical Considerations
- The model assumes that constraints and profit values are accurate and provided in good faith.
- The model does not account for external business or ethical factors, such as sustainability, labor conditions, or regulatory constraints beyond the given inputs.
- Users should verify that optimization outputs align with their business and ethical goals.

## Performance and Limitations
**Performance**:
- The model guarantees optimality if a feasible solution exists.
- Uses OR-Tools' solvers (CBC, SCIP) for efficient resolution.

**Limitations**:
- The model does not handle stochastic or dynamic optimization scenarios.
- It assumes linear constraints and integer decision variables.
- It may be sensitive to input variations and constraint definitions.

## Deployment & MLflow Integration
This model is packaged as an MLflow **pyfunc** model. It can be logged and loaded in MLflow as follows:

```python
import mlflow.pyfunc
model = mlflow.pyfunc.load_model("models:/OptimModel/1")
inputs = {"profit_P1": 5, "profit_P2": 8, "work_limit": 40, "material_limit": 30}
result = model.predict(inputs)
print(result)
```

## Compliance with AI Act
**Risk Category**: Low-risk optimization model under AI Act classifications.
**Explainability**: The model follows a deterministic approach with traceable constraints and results.
**Auditability**: Input-output mapping is well-defined and can be logged in MLflow for traceability.
**Fairness & Bias**: The model does not use personal or sensitive data; decisions are based solely on numerical constraints and profit values.
**Safety & Robustness**: The model is tested with various constraints to ensure stability and correctness.

## Versioning & Updates
Future updates may include:
- Support for continuous variables.
- Integration with additional solvers.
- Expansion to multi-objective optimization.

## Contact & Support
For questions or issues, contact [Your Contact Info].
