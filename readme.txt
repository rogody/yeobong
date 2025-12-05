환경설정

windows
python -m venv .venv
.\.venv\Scripts\activate

mac/linux
python -m venv .venv
source .venv/bin/activate

다운
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

실행
python -m main

DB configuration
RAG\db_config.ini 의 [database] 섹션에 DB 접속 정보를 입력한 뒤 실행하세요. 실제 자격 증명 파일은 git에 올리지 않도록 .gitignore 처리되어 있습니다.


live2d 3.14 호환 안될 때 3.11로 설치환경 셋팅 필요
>> py -3.11 -m venv .venv311
>> .\.venv311\Scripts\activate
>> python --version    # 3.11.x 확인
>> python -m pip install -U pip setuptools wheel
>> python -m pip install -r requirements.txt