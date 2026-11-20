
from odoo import models


class PaymentListPdf(models.AbstractModel):
    _name = 'report.student_management.report_payment_list_pdf'
    _description = 'Payment List PDF Report'

    def _get_report_values(self, docids, data=None):
        data = data or {}

        # Get Payment IDs
        payment_ids = (
            data.get('payment_ids')
            or docids
            or data.get('active_ids')
            or []
        )

        # Get Payment Records
        payments = self.env['school.payment'].browse(
            payment_ids
        ).exists()

        method_label = dict(
            self.env['school.payment']
            ._fields['payment_method'].selection
        )

        state_label = dict(
            self.env['school.payment']
            ._fields['state'].selection
        )

        rows = []
        total = 0.0
        confirmed_total = 0.0

        for payment in payments:
            amount = payment.amount or 0.0

            rows.append({
                'reference': payment.name or '',
                'student_code': payment.student_id.student_code or '',
                'student': payment.student_id.name or '',
                'enrollment': payment.enrollment_id.name or '',
                'date': str(payment.payment_date or ''),
                'method': method_label.get(
                    payment.payment_method, ''
                ),
                'state': state_label.get(
                    payment.state, ''
                ),
                'amount': '{:,.0f}'.format(amount),
            })

            total += amount

            if payment.state == 'confirmed':
                confirmed_total += amount

        return {
            'doc_ids': payments.ids,
            'doc_model': 'school.payment',
            'docs': payments,
            'rows': rows,
            'count': len(rows),
            'total': '{:,.0f}'.format(total),
            'confirmed_total': '{:,.0f}'.format(
                confirmed_total
            ),
            'date_from': data.get('date_from') or 'All',
            'date_to': data.get('date_to') or 'All',
            'method': data.get('method') or 'All',
            'state': data.get('state') or 'All',
        }
