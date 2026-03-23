# Global variables
PROJECT_NAME := test_ia_act
MODEL_NAME := credit_default_predictor
MODEL_VERSION := 6

login:
	uv run mp login --username alice@example.com --password pass!

list-projects:
	uv run mp projects list

list-models:
	uv run mp projects list-models $(PROJECT_NAME)

batch-predict:
	uv run mp batch submit $(PROJECT_NAME) $(MODEL_NAME) $(MODEL_VERSION) --file-path notebooks/banking/Banking\ Credit\ Scoring/batch_prediction_test_credit_default.csv

batch-status:
	@read -p "Enter Job ID: " JOB_ID; \
	uv run mp batch status $(PROJECT_NAME) $$JOB_ID

batch-download:
	@read -p "Enter Job ID: " JOB_ID; \
	uv run mp batch download $(PROJECT_NAME) $$JOB_ID

batch-list:
	uv run mp batch list $(PROJECT_NAME)

run-notebooks:
	./run_notebooks.sh
