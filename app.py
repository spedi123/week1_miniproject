from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

# 각자 로컬에서 돌리고 나중에 꼭 바꿔주세요!!!
client = MongoClient('localhost', 27017)
db = client.dbsparta_plus_week4


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})
        return render_template('index.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)



@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    id_receive = request.form['id_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'id': id_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': id_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    id_receive = request.form['id_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "id": id_receive,
        "password": password_hash,
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    id_receive = request.form['id_give']
    exists = bool(db.users.find_one({"id": id_receive}))
    # print(value_receive, type_receive, exists)
    return jsonify({'result': 'success', 'exists': exists})

@app.route('/gathering_join')
def gathering_join():
    token_receive = request.cookies.get('mytoken')
    try:
        # 복호화 후 쿠키에서 유저 아이디 받아오기
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})

        # 이미 참석하기로 한 모임 리스트, request로 넘겨받은 모임 title 저장
        # str split(',')로 구현 할 예정이라 title에는 ,사용 금지 제약 걸어야
        str_attended = user_info["attended"]
        already_attended = str_attended.split(',')

        title_receive = request.form["title_give"]

        # 토글로 구현, bool값을 request로 전달해서 구분 - 삭제 요청인지 취소 요청인지
        is_cancel = request.form["is_cancel_give"]

        # 삭제 요청시(조건문 필요 없음)
        if is_cancel:
            temp_attended = user_info["attended"]
            temp_attended_list = temp_attended.split(',')
            temp_attended_list.remove(title_receive)
            temp_attended = ','.join(temp_attended_list)
            db.users.update_one({'id': payload["id"]}, {'$set': {'joined': temp_attended}})
            db.gathering_data.delete_one({'id': user_info['id']}, {'gathering_title': title_receive})

            # 모임 정보 db, 유저 정보의 참석 리스트에서 각각 데이터값 삭제 완료 후 jsonify 리턴
            return jsonify({'result' : 'success', "msg" : "모임 참석 취소 완료!"})


        # gatherings db에서 새로 요청한 모임명 찾음, 그리고 시간값 받아와서 변수에 저장
        new_appointment_time = db.gatherings.find_one({"title": title_receive})["date"]

        # gatherings db에서 좀 전에 받아온 user db의 attended 배열에서 해당하는 값을 찾음
        # 찾은 값을 already_attended_time에 저장
        already_attended_time = []
        for i in already_attended:
            already_attended_time.append(db.gatherings.find_one({"title" : i})["date"])

        # 중복값 찾기
        for a in already_attended_time:
            if a == new_appointment_time:
                #참석 불가, 리턴
                return jsonify({"result": "failed", 'msg': '이미 해당 시간에 약속이 존재합니다.'})

        # 이후 각 db에 저장 후
        temp_attended = user_info["attended"]
        if len(temp_attended) >= 1:
            temp_attended.join(',').join(title_receive)
        else :
            temp_attended.join(title_receive)
        db.users.update_one({'id': payload["id"]}, {'$set': {'joined': temp_attended}})

        doc = {
            "title": title_receive,
            "id": user_info["id"]
        }
        db.post_data.insert_one(doc)
        return jsonify({"result" : "success", 'msg' : '조인 완료'})


    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/gatherings', methods=['GET'])
def read_gatherings():
    gatherings = list(db.gatherings.find({}, {'_id': False}))
    return jsonify({'all_gatherings': gatherings})



@app.route('/api/gathering_create', methods=['POST'])
def save_gathering():

    # 모임 저장하기
    title_receive = request.form['title_give']
    date_receive = request.form['date_give']
    agenda_receive = request.form['date_give']
    max_guests_receive = request.form['date_give']
    location_receive = request.form['date_give']
    restaurant_receive = request.form['date_give']

    doc = {
        'title' : title_receive,
        'date' : date_receive,
        'agenda': agenda_receive,
        'max_guests': max_guests_receive,
        'location': location_receive,
        'restaurant': restaurant_receive,
    }

    db.gatherings.insert_one(doc)
    return jsonify({'result': 'success', 'msg': f'{title_receive} 모임 개최 완료!'})












if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
