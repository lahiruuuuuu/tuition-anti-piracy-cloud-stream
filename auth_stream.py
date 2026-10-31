import json
import time
import hashlib

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    student_id = body.get('student_id')
    video_name = body.get('video_name')
    student_mobile = body.get('student_mobile', '07XXXXXXXX')
    device_fingerprint = body.get('device_fingerprint', 'unknown_hw_id')
    
    # NEW PARAMETER: Capture which specific week the student clicked on
    target_week = body.get('target_week', 1) # Default to Week 1 if empty
    
    # SIMULATED DATABASE: Tracking exactly which weeks this student has paid for
    # In a real database, this map updates when the student uploads their monthly/weekly receipt slip
    student_payment_records = {
        "Lahiru": {
            "week_1": True,
            "week_2": True,
            "week_3": False, # Student hasn't paid for Week 3 yet
            "week_4": False  # Student hasn't paid for Week 4 yet
        }
    }
    
    # Fetch this specific student's record out of our database ledger
    student_record = student_payment_records.get(student_id, {})
    week_key = f"week_{target_week}"
    has_paid_for_week = student_record.get(week_key, False)
    
    # 1. Weekly Access Intercept: If they haven't paid for this specific week, block them immediately!
    if not has_paid_for_week:
        return {
            'statusCode': 403,
            'body': json.dumps({
                'error': f'Access Denied: You have not unlocked access for Week {target_week} content yet!'
            })
        }
    
    # 2. Network and Device Binding Logic (If paid for the week)
    request_context = event.get('requestContext', {})
    identity = request_context.get('identity', {})
    student_ip = identity.get('sourceIp', '127.0.0.1')
    
    expiration_time = int(time.time()) + 7200
    secret_salt = "AL_PHYSICS_SALT_2026"
    raw_hash = f"{student_id}{student_ip}{device_fingerprint}{expiration_time}{secret_salt}"
    secure_token = hashlib.sha256(raw_hash.encode()).hexdigest()[:20]
    
    secure_url = f"http://localhost:4566/tuition-premium-videos-local/{video_name}?token={secure_token}&week={target_week}"
    
    # 3. Output structural markers telling the player UI how to lock down the layout canvas
    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'AUTHORIZED',
            'unlocked_week': target_week,
            'streaming_url': secure_url,
            'security_payload': {
                'watermark_text': f"ID: {student_id} | WEEK {target_week} | MOBILE: {student_mobile}",
                'device_lock_id': device_fingerprint,
                'anti_screenshot_enforced': True
            }
        })
    }

