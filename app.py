from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

SECRET_KEY = 'SPARTA'

# 로컬테스트 시 변경 후 진행해주세요.
client = MongoClient('mongodb://test:test@13.125.38.245', 27017)
db = client.meatup

# 변경 시작 18:13
@app.route('/api/endup_gathering', methods=['POST'])
def endup_gathering():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        title_receive = request.form['title_give']
        star_receive = request.form['star_give']
        review_receive = request.form['review_give']
        location_receive = db.gatherings.find_one({'title':title_receive})['location']
        restaurant_receive = db.gatherings.find_one({'title':title_receive})['restaurant']
        date_receive = db.gatherings.find_one({'title':title_receive})['date']
        food_img = db.gatherings.find_one({'title' : title_receive})['food_img']

        doc = {
            'title' : title_receive,
            'date' : date_receive,
            'star' : star_receive,
            'review' : review_receive,
            'location' : location_receive,
            'restaurant' : restaurant_receive,
            'food_img': food_img
        }
        db.endupgathering.insert_one(doc)
        db.gatherings.delete_one({'title' : title_receive})
        return jsonify({'result': 'success', 'msg': f'{title_receive} 모임 종료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
#변경 끝 18:13


#endup 조회APi
@app.route('/api/endup_view')
def endup_view():
    token_receive = request.cookies.get('mytoken')
    try:
        endup_gatherings = list(db.endupgathering.find({}, {'_id': False}))

        return render_template('gathering_details.html', endup_gatherings=endup_gatherings)

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})
        userid = payload["id"]
        gatherings = list(db.gatherings.find({}, {'_id': False}))
        # 모임 잔여인원 구하기
        joind_counter = {}
        for gathering in gatherings:
            # 변경 12:44 - 잔여인원수로 변경함
            joind_counter[gathering['title']] = db.gathering_data.count({'title' : gathering['title']}) + 1
            # 변경 12:44 - 변경 끝
        print(gatherings)
        print(joind_counter)
        # 이래도 보안 문제 없을까?
        return render_template('index.html', userid=userid, user_info=user_info, gatherings=gatherings, joind_counter = joind_counter)
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
         'exp': datetime.utcnow() + timedelta(seconds= 60 * 3 * 60)
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
        "attended": []
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    id_receive = request.form['id_give']
    exists = bool(db.users.find_one({"id": id_receive}))
    # print(value_receive, type_receive, exists)
    return jsonify({'result': 'success', 'exists': exists})

@app.route('/gathering_join', methods = ['POST'])
def gathering_join():
    token_receive = request.cookies.get('mytoken')
    try:
        # 복호화 후 쿠키에서 유저 아이디 받아오기
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})

        # 이미 참석하기로 한 모임 리스트, request로 넘겨받은 모임 title 저장
        attended_receive = user_info["attended"]


        title_receive = request.form["title_give"]
        max_guests = int(db.gatherings.find_one({"title":title_receive})['max_guests'])
        joined_guests = int(db.gathering_data.count({"title" : title_receive}))
        # 토글로 구현, bool값을 request로 전달해서 구분 - 삭제 요청인지 취소 요청인지
        cancel_receive = request.form["is_cancel_give"]
        is_cancel = int(cancel_receive)


        # 삭제 요청시
        if is_cancel == 1:
            if title_receive in attended_receive:
                attended_receive.remove(title_receive)
            else:
                return jsonify({'result' : 'success', "msg" : "참석한 모임이 아닙니다."})
            db.users.update_one({'id': payload["id"]}, {'$set': {'attended': attended_receive}})
            db.gathering_data.delete_one({'id': user_info['id'], 'title' : title_receive})

            # 모임 정보 db, 유저 정보의 참석 리스트에서 각각 데이터값 삭제 완료 후 jsonify 리턴
            return jsonify({'result' : 'success', "msg" : "모임 참석 취소 완료!"})


        # 참석 요청 전 예외처리끝
        #변경-12:44 예외처리 다시 함
        if max_guests <= joined_guests + 1:
            # 변경끝-12:44
            return jsonify({'result': 'success', "msg" : "모임 정원이 가득 찼습니다."})

        # gatherings db에서 새로 요청한 모임명 찾음, 그리고 시간값 받아와서 변수에 저장
        new_appointment_time = db.gatherings.find_one({"title": title_receive})["date"]

        # gatherings db에서 좀 전에 받아온 user db의 attended 배열에서 해당하는 값을 찾음
        # 찾은 값을 already_attended_time에 저장
        already_attended_time = []
        print(len(attended_receive))
        if len(attended_receive) == 0:

            attended_receive.append(title_receive)
            db.users.update_one({'id': payload["id"]}, {'$set': {'attended': attended_receive}})
            doc = {
                "title": title_receive,
                "id": user_info["id"]
            }
            db.gathering_data.insert_one(doc)
            return jsonify({"result": "success", 'msg': '모임 참석 신청 완료'})
        else:
            for i in attended_receive:
                already_attended_time.append(db.gatherings.find_one({"title" : i})["date"])

        for a in already_attended_time:
            if a == new_appointment_time:
                #참석 불가, 리턴
                return jsonify({"result": "success", 'msg': '이미 해당 시간에 약속이 존재합니다.'})

        # 이후 각 db에 저장 후
        attended_receive.append(title_receive)
        db.users.update_one({'id': payload["id"]}, {'$set': {'attended': attended_receive}})
        doc = {
            "title": title_receive,
            "id": user_info["id"]
        }
        db.gathering_data.insert_one(doc)
        return jsonify({"result" : "success", 'msg' : '조인 완료'})


    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

# @app.route('/gatherings', methods=['GET'])
# def read_gatherings():
#     gatherings = list(db.gatherings.find({}, {'_id': False}))
#     return jsonify({'all_gatherings': gatherings})

@app.route('/api/gathering_create', methods=['POST'])
def save_gathering():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        host_receive = payload["id"]
        # 모임 저장하기
        title_receive = request.form['title_give']
        date_receive = request.form['date_give']
        agenda_receive = request.form['agenda_give']
        max_guests_receive = request.form['max_guests_give']
        location_receive = request.form['location_give']
        restaurant_receive = request.form['restaurant_give']
        host_receive = payload["id"]

        # 중복검사
        if db.gatherings.count({'title': title_receive}) > 0:
            return jsonify({'result': 'success', 'msg': f'{title_receive} 모임 제목이 중복되었습니다!'})

        # 9/16. 15:23 restaurant_receive 값 기준으로, 널이면 기본이미지 출력
        if restaurant_receive == '':
            food_img = '../static/sample_img.png'
            print(food_img)

        else:
            url = 'https://www.mangoplate.com/search/' + restaurant_receive
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
            data = requests.get(url, headers=headers)
            soup = BeautifulSoup(data.text, 'html.parser')
            food_img = soup.select_one(
                'body > main > article > div.column-wrapper > div > div > section > div.search-list-restaurants-inner-wrap > ul > li:nth-child(1) > div:nth-child(1) > figure > a > div > img')[
                'data-original']

        doc = {
            'title' : title_receive,
            'date' : date_receive,
            'agenda': agenda_receive,
            'max_guests': max_guests_receive,
            'location': location_receive,
            'restaurant': restaurant_receive,
            'host' : host_receive,
            'food_img': food_img
        }

        db.gatherings.insert_one(doc)
        return jsonify({'result': 'success', 'msg': f'{title_receive} 모임 개최 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


#update 시 user_id는 필요 없음. => 수정버튼 노출여부 결정 시 판단하면 됨
#수정버튼 클릭한 카드의 타이틀을 기준으로 db update
@app.route('/api/update', methods=['POST'])
def update_gathering():
    # 수정하고 싶은 모임의 타이틀을 클라이언트로부터 받아오기
    title_receive = request.form['title_give']
    date_receive = request.form['date_give']
    agenda_receive = request.form['agenda_give']
    max_guests_receive = request.form['max_guests_give']
    location_receive = request.form['location_give']

    # 데이터베이스 업데이트
    db.gatherings.update_one({'title': title_receive},
                             {'$set': {'agenda': agenda_receive,
                                       'date': date_receive,
                                       'max_guests': max_guests_receive,
                                       'location': location_receive,
                                       }})

    # 수정 완료 메세지 띄우기
    return jsonify({'msg': '수정 완료!'})

#삭제버튼 클릭한 카드의 타이틀을 기준으로 delete
@app.route('/api/delete', methods=['POST'])
def delete_gathering():
    title_receive = request.form['title_give']
    db.gatherings.delete_one({'title': title_receive})
    return jsonify({'msg': '삭제 완료!'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
