import random
import time

import requests

# URL de l'endpoint du modèle déployé
ENDPOINT_URL = "http://model-platform.com/deploy/Smart-Grid-Load-Forecasting/smart-grid-load-forecasting-credit-default-predictor-1-d-7e778c/predict"


def generate_random_payload():
    """Génère un payload aléatoire respectant le schéma attendu par le modèle."""
    age = random.randint(22, 70)
    income = random.randint(15000, 150000)
    loan_amount = random.randint(1000, 80000)
    loan_duration_months = random.choice([12, 24, 36, 48, 60, 84])
    credit_score = random.randint(300, 850)
    num_existing_loans = random.randint(0, 6)
    employment_years = random.randint(0, min(35, age - 18))  # Logique basique pour l'ancienneté
    missed_payments_12m = random.randint(0, 5)

    # Ratios dérivés (identiques à la génération du notebook d'origine)
    ratio = round(min(loan_amount / income, 5.0), 4)
    debt_to_income_ratio = ratio
    loan_to_income_ratio = ratio

    # Format attendu par le wrapper FastAPI custom de la Model Platform
    # On force les types en float car le modèle a été entraîné avec des données normalisées (StandardScaler)
    # dont le type inféré par MLflow est 'double' (float64)
    payload = {
        "inputs": {
            "age": float(age),
            "income": float(income),
            "loan_amount": float(loan_amount),
            "loan_duration_months": float(loan_duration_months),
            "credit_score": float(credit_score),
            "num_existing_loans": float(num_existing_loans),
            "employment_years": float(employment_years),
            "missed_payments_12m": float(missed_payments_12m),
            "debt_to_income_ratio": float(debt_to_income_ratio),
            "loan_to_income_ratio": float(loan_to_income_ratio),
        }
    }
    return payload


def main():
    duration_minutes = 5
    end_time = time.time() + (duration_minutes * 60)

    print(f"🚀 Début de la simulation d'appels vers l'endpoint pendant {duration_minutes} minutes...")
    print(f"URL: {ENDPOINT_URL}\n")

    success_count = 0
    error_count = 0
    call_count = 0

    while time.time() < end_time:
        call_count += 1
        payload = generate_random_payload()

        try:
            response = requests.post(
                ENDPOINT_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=5
            )

            if response.status_code == 200:
                print(f"[Appel #{call_count}] ✅ Succès | Prédiction : {response.json()}")
                success_count += 1
            else:
                print(f"[Appel #{call_count}] ❌ Erreur HTTP {response.status_code} | Détails : {response.text}")
                error_count += 1

        except requests.exceptions.RequestException as e:
            print(f"[Appel #{call_count}] ⚠️ Exception réseau : {e}")
            error_count += 1

        # Pause aléatoire entre 0.1 et 10 secondes
        sleep_duration = random.uniform(0.1, 10.0)
        print(f"   ⏳ Attente de {sleep_duration:.2f} s...")
        time.sleep(sleep_duration)

    print("\n📊 Bilan des appels :")
    print(f"Total des appels tentés : {call_count}")
    print(f"✅ {success_count} appels réussis")
    print(f"❌ {error_count} appels en erreur")


if __name__ == "__main__":
    main()
