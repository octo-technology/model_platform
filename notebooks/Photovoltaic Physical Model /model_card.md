# Model Card for PVLib Model

## Model Details
**Name**: PVLibModel
**Version**: 1.0
**Author**: [Your Name or Organization]
**Date**: [YYYY-MM-DD]
**License**: [License Type]
**Model Type**: Solar Energy Prediction Model (PVLib)
**Frameworks**: MLflow, PVLib, Pandas

## Overview
This model utilizes the **PVLib Python** library to simulate the performance of a photovoltaic (PV) system based on meteorological inputs. It predicts the **total AC power output** for a given location using historical or real-time weather data.

## Intended Use
**Primary Use Case**:
- Estimating photovoltaic energy production based on location and weather conditions.
- Supporting solar energy research and system design.
- Analyzing solar potential for specific sites.

**Users**:
- Renewable energy researchers and engineers.
- Data scientists working on solar energy forecasting.
- Companies and institutions assessing solar power feasibility.

## Inputs and Outputs
### Inputs
The model expects a **Pandas DataFrame** with the following columns:
- **latitude** (float): Geographical latitude of the location.
- **longitude** (float): Geographical longitude of the location.
- **name** (str): Site name or identifier.
- **altitude** (float): Altitude of the location (m).
- **timezone** (str): Timezone of the location.

### Outputs
The model returns a **Pandas Series** containing:
- **[Site Name]** (float): Total AC power output (Wh) over the simulation period.

## Ethical Considerations
- The model relies on publicly available weather data sources.
- Predictions depend on accurate input parameters; incorrect inputs may lead to misleading results.
- Not designed for real-time grid integration without further validation and calibration.

## Performance and Limitations
**Performance**:
- Uses PVLib’s well-established solar energy models.
- Weather data is retrieved from **PVGIS**, ensuring reliable radiation estimates.

**Limitations**:
- Performance depends on the quality of input weather data.
- Does not account for shading, dirt, or panel degradation over time.
- Assumes a **fixed-mount system** with optimal tilt based on latitude.

## Deployment & MLflow Integration
This model is packaged as an MLflow **pyfunc** model. It can be logged and loaded in MLflow as follows:

```python
import mlflow.pyfunc
pvlib_model = mlflow.pyfunc.load_model("models:/pvlib_model/1")
import pandas as pd

input_data = pd.DataFrame([{
    "latitude": 45.0, "longitude": -1.0, "name": "Site1",
    "altitude": 10, "timezone": "Europe/Paris"
}])
result = pvlib_model.predict(input_data)
print(result)
```

## Compliance with AI Act
**Risk Category**: Low-risk model under AI Act classifications.
**Explainability**: Based on transparent physical and empirical solar modeling.
**Auditability**: Weather data sources and input parameters can be logged for traceability.
**Fairness & Bias**: No personal data used; model relies on physics-based solar energy calculations.
**Safety & Robustness**: Uses established PVLib methodology with standard assumptions.

## Versioning & Updates
Future updates may include:
- Support for **real-time weather APIs**.
- Integration of **tracking PV systems** instead of fixed mounts.
- Extended validation with diverse geographical datasets.

## Contact & Support
For questions or issues, contact [Your Contact Info].
