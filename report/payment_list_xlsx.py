
from odoo import models


class PaymentListXlsx(models.AbstractModel):
    _name = 'report.student_management.payment_list_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Payment List Excel Report'

    def generate_xlsx_report(self, workbook, data, payments):
        data = data or {}

        sheet = workbook.add_worksheet('Payments')

        # Excel Formats
        title = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
        })

        info = workbook.add_format({
            'italic': True,
        })

        header = workbook.add_format({
            'bold': True,
            'bg_color': '#714B67',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
        })

        cell = workbook.add_format({
            'border': 1,
        })

        money = workbook.add_format({
            'border': 1,
            'num_format': '#,##0',
        })

        total_fmt = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '#,##0',
        })

        # Report Information
        sheet.merge_range('A1:H1', 'Payment Report', title)

        sheet.write(
            'A2',
            'Date: %s ~ %s' % (
                data.get('date_from') or 'All',
                data.get('date_to') or 'All',
            ),
            info,
        )

        sheet.write(
            'D2',
            'Method: %s' % data.get('method', 'All'),
            info,
        )

        sheet.write(
            'F2',
            'Status: %s' % data.get('state', 'All'),
            info,
        )

        # Table Headers
        headers = [
            'Reference',
            'Student ID',
            'Student',
            'Enrollment',
            'Payment Date',
            'Method',
            'Status',
            'Amount (MMK)',
        ]

        for col, header_name in enumerate(headers):
            sheet.write(3, col, header_name, header)

        # Payment Data
        method_label = dict(
            payments._fields['payment_method'].selection
        )

        state_label = dict(
            payments._fields['state'].selection
        )

        row = 4
        total = 0.0
        confirmed_total = 0.0

        for payment in payments:
            amount = payment.amount or 0.0

            sheet.write(row, 0, payment.name or '', cell)
            sheet.write(
                row, 1,
                payment.student_id.student_code or '',
                cell,
            )
            sheet.write(
                row, 2,
                payment.student_id.name or '',
                cell,
            )
            sheet.write(
                row, 3,
                payment.enrollment_id.name or '',
                cell,
            )
            sheet.write(
                row, 4,
                str(payment.payment_date or ''),
                cell,
            )
            sheet.write(
                row, 5,
                method_label.get(payment.payment_method, ''),
                cell,
            )
            sheet.write(
                row, 6,
                state_label.get(payment.state, ''),
                cell,
            )
            sheet.write_number(
                row, 7,
                amount,
                money,
            )

            # Calculate Total
            total += amount

            # Calculate Confirmed Total
            if payment.state == 'confirmed':
                confirmed_total += amount

            row += 1

        # Total Amount
        sheet.write(row, 6, 'Total', total_fmt)
        sheet.write_number(row, 7, total, total_fmt)

        row += 1

        # Confirmed Total Amount
        sheet.write(row, 6, 'Confirmed Total', total_fmt)
        sheet.write_number(
            row, 7,
            confirmed_total,
            total_fmt,
        )

        # Column Width
        sheet.set_column('A:B', 18)
        sheet.set_column('C:D', 22)
        sheet.set_column('E:G', 15)
        sheet.set_column('H:H', 16)
