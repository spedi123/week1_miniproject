from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

SECRET_KEY = 'SPARTA'

# # 각자 로컬에서 돌리고 나중에 꼭 바꿔주세요!!!
# client = MongoClient('localhost', 27017)
# db = client.test_db_for_Youtube3

# 로컬테스트 시 변경 후 진행해주세요.
client = MongoClient('mongodb://test:test@13.125.38.245', 27017)
db = client.meatup

#로그인 페이지 렌더링
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

#로그인 로직
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

#회원가입 로직
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

#회원가입 로직 - 중복 여부 판별
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    id_receive = request.form['id_give']
    exists = bool(db.users.find_one({"id": id_receive}))
    # print(value_receive, type_receive, exists)
    return jsonify({'result': 'success', 'exists': exists})

# 메인 페이지 렌더링
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    # 로그인 안했거나 토큰 만료시 에러발생
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # 토큰 id값 받아서 db에 검색, user 정보를 저장
        user_info = db.users.find_one({"id": payload["id"]})
        userid = payload["id"]

        # gathering db에서 모임 정보 추출
        gatherings = list(db.gatherings.find({}, {'_id': False}))

        # 각 모임별 참석 정원 구하기 위해 딕셔너리 선언 후 db에서 처리 후 저장
        joind_counter = {}
        for gathering in gatherings:
            joind_counter[gathering['title']] = db.gathering_data.count({'title' : gathering['title']})

        # index.html렌더링, id값 전달(Jinja Template if문 사용하기 위해), 모임 데이터 전달(카드 형태로 랜더링), 잔여인원 카운터 한 내용 전달
        return render_template('index.html', userid=userid, user_info=user_info, gatherings=gatherings, joind_counter = joind_counter)

    #로그인 안했거나 토큰 만료시 에러발생
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

# 모임 생성
@app.route('/api/gathering_create', methods=['POST'])
def save_gathering():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # requests로 정보 넘겨받음
        title_receive = request.form['title_give']
        date_receive = request.form['date_give']
        agenda_receive = request.form['agenda_give']
        max_guests_receive = request.form['max_guests_give']
        location_receive = request.form['location_give']
        restaurant_receive = request.form['restaurant_give']
        # ID값은 토큰에서
        host_receive = payload["id"]
        user_info = db.users.find_one({'id' : host_receive})
        host_attended = user_info['attended']
        host_attended_time = []

        # 중복검사 - title을 키값으로 씀, 잔여인원수 계산 등 로직에 사용
        if db.gatherings.count({'title': title_receive}) > 0:
            return jsonify({'result': 'success', 'msg': f'{title_receive} 모임 제목이 중복되었습니다!'})

        if len(host_attended) > 0:
            for i in host_attended:
                host_attended_time.append(db.gatherings.find_one({'title' : i})['date'])

            for j in host_attended_time:
                if j == date_receive:
                    return jsonify({'result': 'success', 'msg': '해당 시간에 이미 참석한 모임이 있어 모임 생성이 불가능합니다!'})


        # img null 값 방지 1
        if restaurant_receive == '':
            food_img = '../static/sample_img.png'

        else:
            url = 'https://www.mangoplate.com/search/' + restaurant_receive
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
            data = requests.get(url, headers=headers)
            soup = BeautifulSoup(data.text, 'html.parser')
            food_img = soup.select_one(
                    'body > main > article > div.column-wrapper > div > div > section > div.search-list-restaurants-inner-wrap > ul > li:nth-child(1) > div:nth-child(1) > figure > a > div > img')[
                    'data-original']

        # img null 값 방지 2
        try:
            doc = {
                'title': title_receive,
                'date': date_receive,
                'agenda': agenda_receive,
                'max_guests': max_guests_receive,
                'location': location_receive,
                'restaurant': restaurant_receive,
                'host': host_receive,
                'food_img': food_img
            }

        except TypeError:
            food_img = '../static/sample_img.png'
            doc = {
                'title': title_receive,
                'date': date_receive,
                'agenda': agenda_receive,
                'max_guests': max_guests_receive,
                'location': location_receive,
                'restaurant': restaurant_receive,
                'host': host_receive,
                'food_img': food_img
            }
        doc2 = {'title': title_receive,
                'id': payload["id"]
        }
        # gatherings db 저장 완료!
        db.gatherings.insert_one(doc)
        host_attended.append(title_receive)
        db.users.update_one({'id': payload["id"]}, {'$set': {'attended': host_attended}})
        db.gathering_data.insert_one(doc2)
        return jsonify({'result': 'success', 'msg': f'{title_receive} 모임 개최 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

# 모임 참여, 여유 될 때 참석요청과 취소요청 별도의 api로 작성하기
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

        # 참석요청인지 취소 요청인지 확인
        cancel_receive = request.form["is_cancel_give"]
        is_cancel = int(cancel_receive)


        # 참석 취소 요청시
        if is_cancel == 1:
            # 유저 db의 attended property(해당 유저가 참석한 모임 명단의 배열값)에서 요청으로 받은 모임title이 있는지 조회
            if title_receive in attended_receive:
                # 있으면 해당값 제거
                attended_receive.remove(title_receive)
            else:
                # 없으면 수정 필요 없음 return으로 함수 종료
                return jsonify({'result' : 'success', "msg" : "참석한 모임이 아닙니다."})

            # 각각의 데이터 db에서 삭제
            db.users.update_one({'id': payload["id"]}, {'$set': {'attended': attended_receive}})
            db.gathering_data.delete_one({'id': user_info['id'], 'title' : title_receive})

            # 모임 정보 db, 유저 정보의 참석 리스트에서 각각 데이터값 삭제 완료 후 jsonify 리턴
            return jsonify({'result' : 'success', "msg" : "모임 참석 취소 완료!"})


        # 정원 초과된 모임에 참여하려는 경우 불가 메시지 alert
        if max_guests <= joined_guests:
            return jsonify({'result': 'success', "msg" : "모임 정원이 가득 찼습니다."})

        # gatherings db에서 새로 요청한 모임명 찾음, 그리고 시간값 받아와서 변수에 저장
        new_appointment_time = db.gatherings.find_one({"title": title_receive})["date"]

        # gatherings db에서 좀 전에 받아온 user db의 attended 배열에서 해당하는 값을 찾음
        # 찾은 값을 already_attended_time에 저장
        already_attended_time = []

        # 참가 요청을 보낸 유저가 참석해 있는 모임이 하나도 없다면
        if len(attended_receive) == 0:
            # 같은 시간대의 모임에 참석하려고 하는지 검증할 필요 없음, 바로 저장 후 성공!
            attended_receive.append(title_receive)
            db.users.update_one({'id': payload["id"]}, {'$set': {'attended': attended_receive}})
            doc = {
                "title": title_receive,
                "id": user_info["id"]
            }
            db.gathering_data.insert_one(doc)
            return jsonify({"result": "success", 'msg': '모임 참석 신청 완료'})
        # 그게 아니고 만약 이미 참석한 모임이 있다면
        else:
            # 검증을 위해 해당 유저가 참가한 모든 모임을 db에 검색해서 예약시간을 배열로 받아옴
            for i in attended_receive:
                already_attended_time.append(db.gatherings.find_one({"title" : i})["date"])

        # 해당 유저가 참석중인 모든 모임의 예약 시간을 저장한 배열에 지금 참석하려는 모임의 예약시간이 있는지 확인함
        for a in already_attended_time:
            if a == new_appointment_time:
                #있으면, 참석 불가
                return jsonify({"result": "success", 'msg': '이미 해당 시간에 약속이 존재합니다.'})

        # 이후 각 db에 저장 후
        attended_receive.append(title_receive)
        db.users.update_one({'id': payload["id"]}, {'$set': {'attended': attended_receive}})
        doc = {
            "title": title_receive,
            "id": user_info["id"]
        }
        db.gathering_data.insert_one(doc)
        return jsonify({"result" : "success", 'msg' : '모임 참석 신청 완료'})


    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))

# 모임 수정, host만 사용 가능한 api
@app.route('/api/update', methods=['POST'])
def update_gathering():
    # 수정하고 싶은 모임의 타이틀을 클라이언트로부터 받아오기
    token_receive = request.cookies.get('mytoken')
    try:
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
                                           'location': location_receive
                                          }})

        # 수정 완료 메세지 띄우기
        return jsonify({'msg': '수정 완료!'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))

# 모임 삭제. host만 사용 가능한 api
@app.route('/api/delete', methods=['POST'])
def delete_gathering():
    try:
        title_receive = request.form['title_give']
        db.gathering_data.remove({'title' : title_receive})
        db.gatherings.delete_one({'title': title_receive})
        return jsonify({'msg': '삭제 완료!'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))

# 모임 포스팅 페이지 렌더링
@app.route('/api/endup_view')
def endup_view():
    token_receive = request.cookies.get('mytoken')
    try:
        endup_gatherings = list(db.endupgathering.find({}, {'_id': False}))

        return render_template('gathering_details.html', endup_gatherings=endup_gatherings)

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))

# 모임 종료 로직, 해당 모임을 포스팅하는 기능도 같이 구현, host만 사용 가능한 api
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

        # 종료된 모임 포스팅용 db, db에 저장
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

        # 기존 모임 정보 & 기존 모임 관련 메타데이터 삭제
        db.gatherings.delete_one({'title' : title_receive})
        db.gathering_data.remove({'title': title_receive})
        return jsonify({'result': 'success', 'msg': f'{title_receive} 모임 종료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
