import json
import hmac
import functools

from odoo import http
from odoo.http import request, Response
from odoo.exceptions import UserError


def require_api_key(func):
    """Request မှာ မှန်ကန်တဲ့ X-API-Key header မပါရင် 401 ပြန်"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        provided = request.httprequest.headers.get('X-API-Key', '')
        expected = request.env['ir.config_parameter'].sudo().get_param(
            'student_management.api_key', '')

        
        valid = bool(expected) and hmac.compare_digest(
            provided.encode('utf-8'), expected.encode('utf-8'))

        if not valid:
            return Response(
                json.dumps({'status': 'error',
                            'message': 'Invalid or missing API key'}),
                content_type='application/json', status=401)
        return func(self, *args, **kwargs)
    return wrapper

def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False),
        content_type='application/json; charset=utf-8',
        status=status)


def float_to_time(value):
    """9.5 -> '09:30'"""
    hours = int(value)
    minutes = int(round((value - hours) * 60))
    return '%02d:%02d' % (hours, minutes)

def student_to_dict(student):
    """ကျောင်းသား တစ်ယောက်ကို JSON ပြောင်းလို့ရတဲ့ dict ပြောင်း"""
    Timetable = request.env['school.timetable'].sudo()
    day_labels = dict(Timetable._fields['day_of_week'].selection)

    # partial/paid enrollment ရှိမှ timetable ပြမယ်
    enrollments = student.enrollment_ids.filtered(
        lambda e: e.payment_status in ('partial', 'paid') and e.class_id)

    timetables = []
    if enrollments:
        records = Timetable.search([
            ('class_id', 'in', enrollments.mapped('class_id').ids),
            ('state', '!=', 'cancelled'),
        ], order='day_of_week, start_time')
        for t in records:
            timetables.append({
                'class': t.class_id.name,
                'subject': t.subject_id.name,
                'teacher': t.teacher_id.name,
                'day': day_labels.get(t.day_of_week, t.day_of_week),
                'start_time': float_to_time(t.start_time),
                'end_time': float_to_time(t.end_time),
                'room': t.room or None,
                'semester': t.semester_id.name,
            })

    return {
        'id': student.id,
        'student_code': student.student_code,
        'name': student.name,
        'gender': student.gender,
        'phone': student.phone or None,
        'email': student.email or None,
        'address': student.address or None,
        'timetable': timetables,
    }

def find_student(student_ref):
    """id (ဂဏန်း) သို့ student_code နဲ့ ရှာ။ မတွေ့ရင် recordset ဗလာပြန်"""
    Student = request.env['school.student'].sudo()
    if student_ref.isdigit():
        return Student.browse(int(student_ref)).exists()
    return Student.search([('student_code', '=', student_ref)], limit=1)


def read_body(kwargs):
    """JSON/text body နဲ့ form-data/query ကို ပေါင်းဖတ်။
    (body, error_response) ပြန်။ error မရှိရင် error_response က None"""
    body = {}
    if request.httprequest.data:
        try:
            body = json.loads(request.httprequest.data)
        except ValueError:
            return None, json_response({
                'status': 'error',
                'message': 'Invalid JSON body',
            }, 400)
        if not isinstance(body, dict):
            return None, json_response({
                'status': 'error',
                'message': 'JSON body must be an object',
            }, 400)
    body.update(kwargs)
    return body, None



#List(GET Method)
class StudentAPI(http.Controller):

    @http.route('/api/students', type='http',
                auth='public', methods=['GET'], csrf=False)
    @require_api_key
    def get_students(self, **kwargs):
        students = request.env['school.student'].sudo().search([], order='id')

        data = []
        for student in students:
            data.append(student_to_dict(student))

        return json_response({
            'status': 'success',
            'message': 'Students retrieved successfully',
            'count': len(data),
            'data': data,
        })
    
    # POST Method
    @http.route('/api/students', type='http',
                auth='public', methods=['POST'], csrf=False)
    @require_api_key
    def create_student(self, **kwargs):
        # 1. Body ဖတ် (JSON/text သို့ form-data နှစ်မျိုးလုံး)
        body = {}
        if request.httprequest.data:
            try:
                body = json.loads(request.httprequest.data)
            except ValueError:
                return json_response({
                    'status': 'error',
                    'message': 'Invalid JSON body',
                }, 400)
            if not isinstance(body, dict):
                return json_response({
                    'status': 'error',
                    'message': 'JSON body must be an object',
                }, 400)
        body.update(kwargs)      # form-data / query param ကိုပါ ပေါင်းထည့်

        name = body.get('name')
        gender = body.get('gender')

        # 2. Validation
        if not name or not gender:
            return json_response({
                'status': 'error',
                'message': 'name and gender are required',
            }, 400)
        if gender not in ('male', 'female'):
            return json_response({
                'status': 'error',
                'message': "gender must be 'male' or 'female'",
            }, 400)

        # 3. Create
        try:
            student = request.env['school.student'].sudo().create({
                'name': name,
                'gender': gender,
                'phone': body.get('phone'),
                'email': body.get('email'),
                'address': body.get('address'),
            })
        except Exception as e:
            return json_response({
                'status': 'error',
                'message': str(e),
            }, 400)

        # 4. Response (GET နဲ့ field တူ၊ data က object တစ်ခု)
        return json_response({
            'status': 'success',
            'message': 'Student created successfully',
            'data': student_to_dict(student),
        }, 201)
    
    #Patch method
    @http.route('/api/students/<string:student_ref>', type='http',
                auth='public', methods=['PATCH'], csrf=False)
    @require_api_key
    def update_student(self, student_ref, **kwargs):
        student = find_student(student_ref)
        if not student:
            return json_response({
                'status': 'error',
                'message': 'Student not found',
            }, 404)

        body, error = read_body(kwargs)
        if error:
            return error

        # ပြင်ခွင့်ပေးမယ့် field တွေပဲ ယူ (whitelist)
        allowed = ['name', 'gender', 'phone', 'email', 'address']
        vals = {k: body[k] for k in allowed if k in body}

        if not vals:
            return json_response({
                'status': 'error',
                'message': 'No valid fields to update. Allowed: '
                           + ', '.join(allowed),
            }, 400)

        if 'name' in vals and not vals['name']:
            return json_response({
                'status': 'error',
                'message': 'name cannot be empty',
            }, 400)
        if 'gender' in vals and vals['gender'] not in ('male', 'female'):
            return json_response({
                'status': 'error',
                'message': "gender must be 'male' or 'female'",
            }, 400)

        try:
            student.write(vals)
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 400)

        return json_response({
            'status': 'success',
            'message': 'Student updated successfully',
            'data': student_to_dict(student),
        })
    
    #PUT method
    @http.route('/api/students/<string:student_ref>', type='http',
                auth='public', methods=['PUT'], csrf=False)
    @require_api_key
    def replace_student(self, student_ref, **kwargs):
        student = find_student(student_ref)
        if not student:
            return json_response({
                'status': 'error',
                'message': 'Student not found',
            }, 404)

        body, error = read_body(kwargs)
        if error:
            return error

        # PUT မှာ required field အားလုံး ပါရမယ်
        required = ['name', 'gender']
        missing = [f for f in required if not body.get(f)]
        if missing:
            return json_response({
                'status': 'error',
                'message': 'PUT requires: ' + ', '.join(missing),
            }, 400)
        if body['gender'] not in ('male', 'female'):
            return json_response({
                'status': 'error',
                'message': "gender must be 'male' or 'female'",
            }, 400)

        # Field အားလုံးကို အစားထိုး (မပို့တဲ့ optional field က ဗလာဖြစ်သွား)
        vals = {
            'name': body['name'],
            'gender': body['gender'],
            'phone': body.get('phone') or False,
            'email': body.get('email') or False,
            'address': body.get('address') or False,
        }

        try:
            student.write(vals)
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 400)

        return json_response({
            'status': 'success',
            'message': 'Student replaced successfully',
            'data': student_to_dict(student),
        })
    
    #DELETE method
    @http.route('/api/students/<string:student_ref>', type='http',
                auth='public', methods=['DELETE'], csrf=False)
    @require_api_key
    def delete_student(self, student_ref, **kwargs):
        student = find_student(student_ref)
        if not student:
            return json_response({
                'status': 'error',
                'message': 'Student not found',
            }, 404)

        if not student.active:
            return json_response({
                'status': 'error',
                'message': 'Student is already archived',
            }, 409)

        try:
            student.write({'active': False})
        except UserError as e:
            # unfinished enrollment ရှိနေရင် model rule က တားတာ
            return json_response({'status': 'error', 'message': e.args[0]}, 409)
        except Exception as e:
            return json_response({'status': 'error', 'message': str(e)}, 400)

        return json_response({
            'status': 'success',
            'message': 'Student archived successfully',
            'data': {
                'id': student.id,
                'student_code': student.student_code,
            },
        })