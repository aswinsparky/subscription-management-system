# Brightloop Nexus — Database Architecture & ER Design
**Member 1: Subscription & Intelligence Engine**
**Database Engine**: MySQL 8.0+ (InnoDB Storage Engine)
**Driver**: PyMySQL with SQLAlchemy 2.0
**Migration Tool**: Alembic
**Monetary Precision**: `DECIMAL(12, 2)`

---

## 1. Relational Database Concepts for Beginners

When building financial and subscription systems, data integrity is paramount:

1. **Storage Engine (InnoDB)**:
   - Provides ACID compliance (Atomicity, Consistency, Isolation, Durability).
   - Guarantees crash recovery and transaction rollback. If any step of subscription activation fails, changes are completely rolled back.
   - Enforces foreign key constraints at the database engine level.

2. **Monetary Precision (`DECIMAL(12, 2)`)**:
   - Floating point numbers (`FLOAT`, `DOUBLE`) suffer from binary representation rounding errors (e.g., `0.1 + 0.2 = 0.30000000000000004`).
   - `DECIMAL(12, 2)` stores exact fixed-point base-10 numbers, ensuring zero financial discrepancy during plan pricing, discounts, and renewal calculations.

3. **Character Set (`utf8mb4`) & Collation (`utf8mb4_unicode_ci`)**:
   - Supports 4-byte UTF-8, including international names, multilingual company names, and emojis without data corruption.

4. **Primary Keys & Foreign Keys**:
   - `id INT AUTO_INCREMENT PRIMARY KEY`: Ensures each record has a unique, fast-indexing identifier.
   - `FOREIGN KEY (customer_id) REFERENCES customers(id)`: Prevents orphaned records. A subscription cannot point to a non-existent customer.

5. **Indexes**:
   - Added on columns frequently searched or filtered: `email`, `subscription_number`, `quotation_number`, `status`, and foreign keys.

---

## 2. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    ROLES ||--o{ USERS : "assigned to"
    USERS ||--o{ PASSWORD_RESET_TOKENS : "requests"
    USERS ||--o| CUSTOMERS : "authenticates as"
    CUSTOMERS ||--o{ QUOTATIONS : "requests"
    CUSTOMERS ||--o{ SUBSCRIPTIONS : "owns"
    CUSTOMERS ||--o{ CHURN_RISK_ASSESSMENTS : "evaluated for"

    PRODUCTS ||--o{ PRODUCT_VARIANTS : "has variants"
    PRODUCTS ||--o{ QUOTATION_ITEMS : "included in"
    PRODUCT_VARIANTS ||--o{ QUOTATION_ITEMS : "specified in"
    PRODUCTS ||--o{ SUBSCRIPTION_ITEMS : "included in"
    PRODUCT_VARIANTS ||--o{ SUBSCRIPTION_ITEMS : "specified in"

    PLANS ||--o{ QUOTATION_TEMPLATES : "default plan for"
    PLANS ||--o{ QUOTATIONS : "defines interval/price for"
    PLANS ||--o{ SUBSCRIPTIONS : "governs lifecycle of"

    QUOTATION_TEMPLATES ||--o{ QUOTATION_TEMPLATE_ITEMS : "contains"
    QUOTATION_TEMPLATES ||--o{ QUOTATIONS : "scaffolds"
    QUOTATIONS ||--o{ QUOTATION_ITEMS : "contains"
    QUOTATIONS ||--o| SUBSCRIPTIONS : "converts into"

    SUBSCRIPTIONS ||--o{ SUBSCRIPTION_ITEMS : "contains"
    SUBSCRIPTIONS ||--o{ SUBSCRIPTION_EVENTS : "audit history (Time Machine)"
    SUBSCRIPTIONS ||--o{ RENEWAL_BILLING_REQUESTS : "triggers invoicing"

    USERS ||--o{ SUBSCRIPTION_EVENTS : "triggers"
    USERS ||--o{ QUOTATIONS : "created by staff/admin"

    ROLES {
        int id PK
        string name UK "ADMIN | STAFF | CUSTOMER"
        string description
    }

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        int role_id FK
        boolean is_active
        datetime created_at
    }

    CUSTOMERS {
        int id PK
        string customer_code UK
        int user_id FK "Nullable linked user"
        string full_name
        string email
        string phone
        string company_name
        text billing_address
        string tax_id
        string account_status "ACTIVE | SUSPENDED | ARCHIVED"
        datetime created_at
    }

    PRODUCTS {
        int id PK
        string product_code UK
        string name
        string product_type "SERVICE | SOFTWARE | HARDWARE | CONSUMABLE"
        decimal sales_price "DECIMAL(12,2)"
        decimal cost_price "DECIMAL(12,2)"
        boolean is_active
        datetime created_at
    }

    PRODUCT_VARIANTS {
        int id PK
        int product_id FK
        string variant_name "e.g. Standard, Odoo, Enterprise"
        string sku UK
        decimal additional_price "DECIMAL(12,2)"
        boolean is_active
    }

    PLANS {
        int id PK
        string plan_code UK
        string name
        string billing_interval "DAILY | WEEKLY | MONTHLY | YEARLY"
        decimal plan_price "DECIMAL(12,2)"
        int minimum_quantity
        datetime available_from
        datetime available_until
        boolean auto_close_enabled
        boolean early_cancellation_allowed
        boolean pause_allowed
        boolean renewal_allowed
        string status "DRAFT | ACTIVE | ARCHIVED"
    }

    QUOTATIONS {
        int id PK
        string quotation_number UK
        int customer_id FK
        int plan_id FK
        datetime quotation_date
        datetime expiration_date
        decimal subtotal "DECIMAL(12,2)"
        string tax_reference
        decimal tax_amount "DECIMAL(12,2)"
        decimal total "DECIMAL(12,2)"
        string status "DRAFT | SENT | ACCEPTED | EXPIRED | REJECTED"
        int converted_to_subscription_id UK "Prevents duplicate conversion"
    }

    SUBSCRIPTIONS {
        int id PK
        string subscription_number UK
        int customer_id FK
        int plan_id FK
        int source_quotation_id FK
        datetime start_date
        datetime expiry_date
        string billing_interval
        string payment_terms
        decimal subtotal "DECIMAL(12,2)"
        decimal discount_amount "DECIMAL(12,2)"
        decimal total_amount "DECIMAL(12,2)"
        string status "DRAFT | QUOTATION | CONFIRMED | ACTIVE | PAUSED | CANCELLED | CLOSED"
        datetime next_billing_date
        boolean auto_renew
    }

    SUBSCRIPTION_EVENTS {
        int id PK
        int subscription_id FK
        string event_type "Time Machine Event"
        json previous_state
        json new_state
        int actor_id FK
        datetime created_at "Append-only"
    }

    CHURN_RISK_ASSESSMENTS {
        int id PK
        int customer_id FK
        int risk_score "0 to 100"
        string risk_classification "LOW | MEDIUM | HIGH"
        text risk_explanation
        text recommended_action
        json signal_breakdown
        datetime assessed_at
    }

    RENEWAL_BILLING_REQUESTS {
        int id PK
        string idempotency_key UK
        int subscription_id FK
        int customer_id FK
        decimal amount "DECIMAL(12,2)"
        string status "PENDING | PROCESSED | FAILED"
        string invoice_reference "Member 2 Hand-off"
    }
```

---

## 3. Coordinated Hand-off with Member 2 (Financial Engine)

| Responsibility | Owner | Integration Contract |
|---|---|---|
| Customer Profile & Address | **Member 1** | Exposes customer ID, billing address, tax identification |
| Plan, Products & Quantities | **Member 1** | Exposes subscription items, pricing, billing interval |
| Renewal Trigger & Due Subscriptions | **Member 1** | Exposes `GET /api/v1/renewals/due` with `idempotency_key` |
| Tax Calculations & Rules | **Member 2** | Member 1 calls `POST /api/v1/taxes/calculate` or references tax rule IDs |
| Invoices & Line Items | **Member 2** | Member 2 creates Invoices matching Member 1's subscription items |
| Payment Collection & Gateways | **Member 2** | Member 2 processes transactions and reconciliation |
| Churn Payment Signals | **Member 2** | Member 2 exposes failed payment count and days overdue for Churn Radar |

