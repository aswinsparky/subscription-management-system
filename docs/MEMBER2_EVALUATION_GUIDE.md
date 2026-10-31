# BRIGHTLOOP NEXUS — FINANCIAL INTELLIGENCE EVALUATION & TESTING GUIDE
## Financial & Revenue Intelligence Engine

**Author:** swetha100504 (`swetha100504@gmail.com`)  
**Role:** Financial & Revenue Intelligence Architect  
**Project:** Brightloop Nexus  

---

## 1. Quick Start / Demo in 60 Seconds

### Step 1: Populate Realistic Financial Demo Data
Run the custom seeder from the project root:
```bash
python backend/seed_financial_demo.py
```
This populates:
- **Taxes**: Standard GST (18%) and Zero-rated export tax (0%).
- **Discounts**: `SAVE20` (20% off) and `WELCOME10` ($10 fixed discount).
- **Invoices**: Multiple invoices across `DRAFT`, `CONFIRMED`, `PAID`, and `OVERDUE` states with detailed line items, discounts, and taxes.
- **Payments**: Full, partial, and bank transfer payments.
- **Reconciliations**: Automatically matched and discrepancy-flagged records.
- **Revenue Guardian**: Detected revenue leak findings ready for review.

---

## 2. Testing Financial Intelligence Modules Step-by-Step

### 1. Taxes & Discounts
- Navigate to the **Taxes & Discounts** tab in the UI (`/taxes-discounts`).
- Create a new percentage or fixed tax.
- Validate coupon codes against minimum spend thresholds (`POST /api/v1/discounts/validate`).
- Verify historical freeze: editing a tax rate will **never** alter existing confirmed invoices.

### 2. Automatic Invoice Generation
- Navigate to **Invoices** (`/invoices`).
- Click **Generate From Active Subscriptions**.
- The system checks billing cycle eligibility, calculates pro-rated or interval lines, applies discounts before tax, calculates tax breakdown, and creates sequential invoices (`INV-YYYY-XXXXXX`).
- Click the button a second time: the idempotency engine prevents duplicate invoices from being generated for the same cycle.

### 3. ReportLab PDF Generation
- In the **Invoices** table, click the **PDF** icon on any invoice or visit:
  `http://localhost:8000/api/v1/invoices/{id}/pdf`
- A branded, publication-grade PDF invoice is rendered dynamically with company letterhead, client address, tabular item breakdowns, tax breakdowns, discount savings, and payment status badges.

### 4. Payments & Simulated Gateway
- Navigate to **Payments** (`/payments`).
- Click **Record Payment**.
- Select an invoice, enter an amount, and choose a method (Card, UPI, Bank Transfer, Cash).
- Test partial payment: Notice how the invoice's outstanding balance drops and status updates accurately without reaching `PAID` until full payment is received.
- Toggle **Simulate Payment Failure** to test gateway error handling.

### 5. Payment Reconciliation
- Navigate to **Reconciliation** (`/reconciliation`).
- View matched payments and auto-flagged discrepancies (Overpaid, Underpaid, Unmatched).
- Click **Resolve Discrepancy** to record supervisor audit notes and mark resolved.

### 6. Revenue Guardian (Autonomous Revenue Leak Detection)
- Navigate to **Revenue Guardian** (`/revenue-guardian`).
- Click **Run Autonomous Audit**.
- The engine scans the database for:
  - Active subscriptions missing invoices.
  - Invoices lingering past due dates.
  - Payment discrepancies.
  - Expired coupon leaks.
  - High churn-risk accounts with overdue balances.
- Each finding includes estimated dollar loss, root-cause explanation, and recommended recovery action.

### 7. Future Revenue Simulator
- Navigate to **Revenue Simulator** (`/revenue-simulator`).
- Adjust interactive sliders:
  - New customers per month
  - Churn rate %
  - Plan upgrade rate %
  - Price change %
  - Projection timeframe (up to 36 months)
- The Recharts visualizer recalculates projected MRR/ARR and expansion vs. churn curves in real time.

### 8. Ask Brightloop AI Assistant
- Navigate to **Ask Brightloop AI** (`/ai-assistant`).
- Click one of the pre-built prompt pills or ask:
  - *"What is our total overdue amount and collection rate?"*
  - *"How much revenue was collected this month?"*
  - *"What are our active subscriptions and total MRR?"*
- Answers are generated using Gemini API or grounded SQL analytical aggregations.

### 9. Revenue Command Center
- Navigate to **Revenue Command Center** (`/revenue-dashboard`).
- View live aggregate KPIs: MRR, ARR, Total Recognized Revenue, Cash Collected, Receivables, Overdue Amount, and Net Collection Rate.

### 10. Self-Healing Billing Recovery
- Navigate to **Billing Recovery** (`/billing-recovery`).
- Review smart dunning schedules (Day 1, Day 3, Day 5 retries) for failed transactions and trigger immediate payment re-attempts.

---

## 3. Running Automated Tests
Run the entire backend test suite:
```bash
pytest backend/tests -v
```
**Expected Result**: All 54 tests pass (100% pass rate).
