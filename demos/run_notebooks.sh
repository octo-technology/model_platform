#!/bin/bash
# Author: Octo Technology MLOps Tribe
# Run all AI Act demo notebooks sequentially via papermill

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/notebooks/output"
mkdir -p "$OUTPUT_DIR"

NOTEBOOKS=(
  "notebooks/banking/Banking Credit Scoring/credit_scoring_ai_act.ipynb"
  "notebooks/banking/Customer Segmentation/customer_segment_classifier_ai_act.ipynb"
  "notebooks/banking/Transaction Fraud Detection/transaction_fraud_ai_act.ipynb"
  "notebooks/banking/Transaction Fraud Detection/transaction_anomaly_ai_act.ipynb"
  "notebooks/ecommerce/Ecommerce Recommendation/product_recommender_ai_act.ipynb"
  "notebooks/ecommerce/Ecommerce Recommendation/customer_churn_predictor_ai_act.ipynb"
  "notebooks/hr/Employee Attrition Prediction/employee_attrition_ai_act.ipynb"
  "notebooks/hr/Employee Attrition Prediction/satisfaction_scorer_ai_act.ipynb"
  "notebooks/medical/Medical Document NLP/document_type_classifier_ai_act.ipynb"
  "notebooks/medical/Medical Document NLP/clinical_entity_extractor_ai_act.ipynb"
  "notebooks/supply_chain/Supply Chain Optimization/demand_forecaster_ai_act.ipynb"
  "notebooks/supply_chain/Supply Chain Optimization/supplier_risk_scorer_ai_act.ipynb"
)

TOTAL=${#NOTEBOOKS[@]}
PASSED=0
FAILED=0
FAILED_LIST=()

cd "$SCRIPT_DIR"

for i in "${!NOTEBOOKS[@]}"; do
  NB="${NOTEBOOKS[$i]}"
  NAME=$(basename "$NB" .ipynb)
  DIR=$(dirname "$NB")
  NUM=$((i + 1))

  echo ""
  echo "=== [$NUM/$TOTAL] $NAME ==="

  if uv run papermill "$NB" "$OUTPUT_DIR/${NAME}_out.ipynb" --cwd "$DIR" 2>&1; then
    echo "PASS: $NAME"
    PASSED=$((PASSED + 1))
  else
    echo "FAIL: $NAME"
    FAILED=$((FAILED + 1))
    FAILED_LIST+=("$NAME")
  fi
done

echo ""
echo "========================================="
echo "Results: $PASSED/$TOTAL passed, $FAILED failed"

if [ $FAILED -gt 0 ]; then
  echo "Failed notebooks:"
  for f in "${FAILED_LIST[@]}"; do echo "  - $f"; done
  exit 1
fi
