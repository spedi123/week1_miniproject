## week1_miniproject
Group 7 Mini Project

Last Update : 9/17

## Project Title
MEAT-UP

## Project Description
Let's Meet(Meat) up!
새로운 사람들과 맛집에서 즐거운 시간을 보내는 모임을 만들고 참가할 수 있는 웹서비스 입니다.
Gathering with new people at restaurant and enjoying meal by webservice.
이 뿐만 아니라 주최자는 모임을 마친 후 모임에 대한 후기를 남길 수 있어서 서비스 이용자들과 모임 경험과 음식점에 대한 정보를 공유할 수 있습니다.
A perosn who made gathering group can write review, so people can share their exprience. 

## Website Link
http://tpservice.shop/(Not availabe now)

## Wesite Video
https://youtu.be/8SDGsYM4nNM

## Stack
Front-end : Jinja, Bulma
Back-end : Flask

### **00. Intro**

1. ***Meat-up*은 사용자들이 맛집 방문 목적 모임을 만들 목적으로 제작된 서비스 입니다**
2. **사용자들은 회원가입 이후 서비스를 사용 할 수 있습니다**
3. **로그인 이후 예약한 음식점의 *음식점 이름*, *예약 일자*, *예약 정원*, *음식점과 관련된 정보*와 *모임 타이틀*을 입력 후 모임을 개최 할 수 있습니다**
4. **생성된 모임과 관련하여 *모임의 호스트는* 모임의 *수정*, *삭제*, *끝내기*의 권한을 가지며 *호스트가 아닌 경우* 참석버튼을 통해 해당 모임에 *참석* 할 수 있습니다.**
5. **생성된 모임에 참여하려는 경우 *정원이 가득 찼거나, 같은 예약 날짜에 다른 Meat-up-gathering에 참여하신 경우* 참석을 할 수 없습니다.**
6. **식당을 다녀와서 호스트가 모임을 끝내는 경우, *모임 참여 인원의 의견을 종합하여 포스팅 페이지에 별점과 후기를 작성하면 모임 후기가 포스팅되어 공유됩니다!***

### **01. 기본 공통 기능**

1. **로그인 페이지 - 회원가입, 로그아웃 버튼**
2. **모임작성 기능**
3. **이미지 크롤링 - 음식점 상호, 음식 종류등을 입력시 모임 이미지에 크롤링**
4. **모임 자세히 보기**

### **02. 호스트가 아닌 경우 전용 기능**

1. **모임 자세히 보기 → 버튼이 '참석' '참석취소'로 표기됨**
2. **모임 참석하기 → 참석 후 모임 카드에 잔여정원 바뀜**
3. **모임 참석하기 2 → 동일 일자에 다른 모임을 참석한 경우 참석안됨 alert 메시지**
4. **모임 참석취소 → 참석 취소 후 잔여정원 바뀜**
5. **모임 정원 가득 찬 경우 모임 참석 불가능**

### **03. 모임 호스트 전용 기능**

1. **모임 자세히 보기 → 버튼이 '수정','삭제','모임 끝' 으로 바뀜**
2. **모임 수정 → 모임 수정기능**
3. **모임 삭제 → 모임 삭제기능**
4. **모임 끝내기 → 리뷰 내용과 별점 입력 → 끝낸 모임 페이지에 카드형식으로 포스팅됨**

### **04. Outro**

***Made by*
Juhyeok Yang, Seonggyu An, Yeongjoon Kwon, Junkyu Kang

*개선사항, 한계점***
- **api 로직의 역할이 명확하게 구분, 분리되어 있지 않음. ex) 하나의 api가 너무 다양한 기능을 구현함**
- **확장등 코드의 변경이 필요할 경우 구현이 더욱 복잡해짐**
