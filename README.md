<<<<<<< HEAD
# TrustLedger-AI — Risk-Aware Autonomy Layer for Financial AI Agents

A working hackathon prototype of the 15-module Decision Governor architecture.
All financial transactions are **simulated** — nothing here touches a real
bank account, wallet, or blockchain.

See `PROJECT_DOCUMENTATION.md` (in the parent folder / provided separately)
for the full write-up: problem statement, architecture, risk-scoring
methodology, AI/ML component breakdown, database design, demo script, and
judge Q&A.

## Quick start

```bash
cd financial-agent-security
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit if you want to set a real JWT_SECRET

python database/seed_data.py     # creates app.db with demo agents/roles/policies
python app.py                    # starts the server on http://localhost:5000
```

Open **http://localhost:5000/dashboard** — click any of the scenario buttons
at the top to fire a pre-built financial-agent intent through all 15 modules
and watch it land as EXECUTE / CONSTRAIN / ESCALATE / BLOCK in real time.

## Calling the API directly

```bash
curl -X POST http://localhost:5000/agent/intent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token-payments-07" \
  -d '{
        "agent_id": "AP_Payments_Agent_07",
        "action_type": "transfer",
        "amount": 5000,
        "currency": "INR",
        "destination": "Vendor_Kumar",
        "instruction": "Transfer INR 5000 to our approved supplier for the June invoice."
      }'
```

Demo agent tokens (also printed by `seed_data.py`):

| Agent | Token |
|---|---|
| AP_Payments_Agent_07 | `demo-token-payments-07` |
| Treasury_Rebalancer_01 | `demo-token-treasury-01` |
| DeFi_Yield_Agent_03 | `demo-token-defi-03` |

## Project layout

See `PROJECT_DOCUMENTATION.md` Part 19 for the full annotated folder
structure. In short: `modules/` holds one file per pipeline stage (1–15),
`routes/` exposes them over HTTP, `ml/` isolates every AI/ML-touching piece,
and `templates/` + `static/` render the live dashboard.

## Resetting the demo

```bash
rm app.db
python database/seed_data.py
```
=======
# TrustLedger-AI
>>>>>>> 8695f9fd43aca648a3b21a9174b102cdfe3981dc
