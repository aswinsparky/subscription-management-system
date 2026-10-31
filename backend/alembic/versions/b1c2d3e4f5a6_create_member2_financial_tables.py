"""create_member2_financial_tables

Revision ID: b1c2d3e4f5a6
Revises: afdefb9d81d1
Create Date: 2026-10-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'afdefb9d81d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. taxes
    op.create_table('taxes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tax_type', sa.String(length=20), nullable=False),
        sa.Column('rate', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('applicability', sa.String(length=50), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('rate >= 0', name='chk_tax_rate_non_negative'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_taxes_name'), 'taxes', ['name'], unique=False)
    op.create_index(op.f('ix_taxes_is_active'), 'taxes', ['is_active'], unique=False)

    # 2. discounts
    op.create_table('discounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('coupon_code', sa.String(length=50), nullable=False),
        sa.Column('discount_type', sa.String(length=20), nullable=False),
        sa.Column('discount_value', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('min_purchase_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('min_quantity', sa.Integer(), nullable=False),
        sa.Column('max_usage_limit', sa.Integer(), nullable=True),
        sa.Column('usage_per_customer_limit', sa.Integer(), nullable=True),
        sa.Column('current_usage_count', sa.Integer(), nullable=False),
        sa.Column('applicable_product_ids', sa.JSON(), nullable=True),
        sa.Column('applicable_plan_ids', sa.JSON(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('discount_value >= 0', name='chk_discount_value_non_negative'),
        sa.CheckConstraint('min_purchase_amount >= 0', name='chk_discount_min_purchase_non_negative'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discounts_coupon_code'), 'discounts', ['coupon_code'], unique=True)
    op.create_index(op.f('ix_discounts_is_active'), 'discounts', ['is_active'], unique=False)

    # 3. invoices
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('invoice_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('billing_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('amount_paid', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('amount_due', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_terms', sa.String(length=100), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('subtotal >= 0', name='chk_inv_subtotal_non_negative'),
        sa.CheckConstraint('discount_amount >= 0', name='chk_inv_discount_non_negative'),
        sa.CheckConstraint('tax_amount >= 0', name='chk_inv_tax_non_negative'),
        sa.CheckConstraint('total_amount >= 0', name='chk_inv_total_non_negative'),
        sa.CheckConstraint('amount_paid >= 0', name='chk_inv_paid_non_negative'),
        sa.CheckConstraint('amount_due >= 0', name='chk_inv_due_non_negative'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoices_invoice_number'), 'invoices', ['invoice_number'], unique=True)
    op.create_index(op.f('ix_invoices_customer_id'), 'invoices', ['customer_id'], unique=False)
    op.create_index(op.f('ix_invoices_subscription_id'), 'invoices', ['subscription_id'], unique=False)
    op.create_index(op.f('ix_invoices_status'), 'invoices', ['status'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_date'), 'invoices', ['invoice_date'], unique=False)
    op.create_index(op.f('ix_invoices_due_date'), 'invoices', ['due_date'], unique=False)
    op.create_index(op.f('ix_invoices_idempotency_key'), 'invoices', ['idempotency_key'], unique=True)

    # 4. invoice_items
    op.create_table('invoice_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('product_variant_id', sa.Integer(), nullable=True),
        sa.Column('subscription_item_id', sa.Integer(), nullable=True),
        sa.Column('item_description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tax_rate_snapshot', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tax_amount_snapshot', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint('quantity >= 1', name='chk_inv_item_qty_positive'),
        sa.CheckConstraint('unit_price >= 0', name='chk_inv_item_price_non_negative'),
        sa.CheckConstraint('subtotal >= 0', name='chk_inv_item_subtotal_non_negative'),
        sa.CheckConstraint('total_amount >= 0', name='chk_inv_item_total_non_negative'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['subscription_item_id'], ['subscription_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_items_invoice_id'), 'invoice_items', ['invoice_id'], unique=False)

    # 5. invoice_tax_details
    op.create_table('invoice_tax_details',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('tax_id', sa.Integer(), nullable=True),
        sa.Column('tax_name_snapshot', sa.String(length=100), nullable=False),
        sa.Column('tax_rate_snapshot', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('calculated_tax_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tax_id'], ['taxes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_tax_details_invoice_id'), 'invoice_tax_details', ['invoice_id'], unique=False)

    # 6. invoice_discount_details
    op.create_table('invoice_discount_details',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('discount_id', sa.Integer(), nullable=True),
        sa.Column('coupon_code_snapshot', sa.String(length=50), nullable=False),
        sa.Column('discount_type_snapshot', sa.String(length=20), nullable=False),
        sa.Column('discount_rate_or_value', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('calculated_discount_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['discount_id'], ['discounts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_discount_details_invoice_id'), 'invoice_discount_details', ['invoice_id'], unique=False)

    # 7. discount_usages
    op.create_table('discount_usages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('discount_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('discount_amount_applied', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['discount_id'], ['discounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discount_usages_discount_id'), 'discount_usages', ['discount_id'], unique=False)
    op.create_index(op.f('ix_discount_usages_customer_id'), 'discount_usages', ['customer_id'], unique=False)

    # 8. invoice_generation_logs
    op.create_table('invoice_generation_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('billing_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('billing_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_generation_logs_subscription_id'), 'invoice_generation_logs', ['subscription_id'], unique=False)

    # 9. payments
    op.create_table('payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payment_reference', sa.String(length=50), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('recorded_by_user_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('payment_status', sa.String(length=50), nullable=False),
        sa.Column('transaction_id', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('amount > 0', name='chk_payment_amount_positive'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['recorded_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_payment_reference'), 'payments', ['payment_reference'], unique=True)
    op.create_index(op.f('ix_payments_invoice_id'), 'payments', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_payments_customer_id'), 'payments', ['customer_id'], unique=False)
    op.create_index(op.f('ix_payments_payment_date'), 'payments', ['payment_date'], unique=False)
    op.create_index(op.f('ix_payments_idempotency_key'), 'payments', ['idempotency_key'], unique=True)

    # 10. payment_reconciliations
    op.create_table('payment_reconciliations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('reconciled_by_user_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('invoice_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discrepancy_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('reconciled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reconciled_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_reconciliations_status'), 'payment_reconciliations', ['status'], unique=False)

    # 11. revenue_guardian_findings
    op.create_table('revenue_guardian_findings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('issue_code', sa.String(length=50), nullable=False),
        sa.Column('issue_title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('estimated_loss', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=False),
        sa.Column('resolution_status', sa.String(length=50), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.CheckConstraint('estimated_loss >= 0', name='chk_guardian_loss_non_negative'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_revenue_guardian_findings_issue_code'), 'revenue_guardian_findings', ['issue_code'], unique=False)
    op.create_index(op.f('ix_revenue_guardian_findings_category'), 'revenue_guardian_findings', ['category'], unique=False)
    op.create_index(op.f('ix_revenue_guardian_findings_severity'), 'revenue_guardian_findings', ['severity'], unique=False)
    op.create_index(op.f('ix_revenue_guardian_findings_resolution_status'), 'revenue_guardian_findings', ['resolution_status'], unique=False)

    # 12. revenue_guardian_runs
    op.create_table('revenue_guardian_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_type', sa.String(length=50), nullable=False),
        sa.Column('triggered_by_user_id', sa.Integer(), nullable=True),
        sa.Column('issues_found_count', sa.Integer(), nullable=False),
        sa.Column('critical_count', sa.Integer(), nullable=False),
        sa.Column('high_count', sa.Integer(), nullable=False),
        sa.Column('estimated_leakage_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['triggered_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 13. billing_recovery_attempts
    op.create_table('billing_recovery_attempts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('failure_type', sa.String(length=50), nullable=False),
        sa.Column('failure_reason', sa.String(length=255), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recovery_status', sa.String(length=50), nullable=False),
        sa.Column('idempotency_key', sa.String(length=120), nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_billing_recovery_attempts_recovery_status'), 'billing_recovery_attempts', ['recovery_status'], unique=False)
    op.create_index(op.f('ix_billing_recovery_attempts_idempotency_key'), 'billing_recovery_attempts', ['idempotency_key'], unique=True)

    # 14. revenue_simulation_scenarios
    op.create_table('revenue_simulation_scenarios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scenario_name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('baseline_mrr', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('projected_mrr', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('net_mrr_impact', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('baseline_arr', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('projected_arr', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('assumptions_json', sa.JSON(), nullable=True),
        sa.Column('monthly_forecast_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('revenue_simulation_scenarios')
    op.drop_table('billing_recovery_attempts')
    op.drop_table('revenue_guardian_runs')
    op.drop_table('revenue_guardian_findings')
    op.drop_table('payment_reconciliations')
    op.drop_table('payments')
    op.drop_table('invoice_generation_logs')
    op.drop_table('discount_usages')
    op.drop_table('invoice_discount_details')
    op.drop_table('invoice_tax_details')
    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('discounts')
    op.drop_table('taxes')

