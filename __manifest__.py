
{
    'name': 'Student Management System',
    'version': '15.0.1.0.0',
    'summary': 'Manage Students, Payments and Academic Information',
    'category': 'Education',
    'depends': [
        'base',
        'web',
        'mail',
        'report_xlsx',
    ],

    'data': [
        'security/security.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/semester_cron.xml',
        'views/student_views.xml',
        'views/payment_views.xml',
        'views/class_views.xml',
        'views/enrollment_views.xml',
        'views/subject_views.xml',
        'views/timetable_views.xml',
        'views/teacher_views.xml',
        'views/semester_views.xml',
        'views/menu_views.xml',            
        'wizard/payment_report_wizard_views.xml', 
        'report/payment_list_pdf.xml',
        'report/payment_list_xlsx.xml',
    ],

    'installable': True,
    'application': True,
}
