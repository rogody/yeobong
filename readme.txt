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

실시간 RAG 저장
main.py가 DBClient/EmbeddingClient/MemoryStore/MemoryRetriever를 초기화하여 UI에서 채팅을 시작하면 각 발화가 conversations/messages/message_chunks 및 embedding 테이블에 자동으로 적재됩니다. DB 연결에 실패하면 경고만 출력하고 기존 메모리 모드로 계속 동작합니다.

청크/검색 파라미터
환경 변수로 RAG_CHUNK_SIZE(기본 250), RAG_CHUNK_OVERLAP(기본 0.2), RAG_RETRIEVE_TOP_K(기본 4)를 지정해 청크 단위·오버랩·검색 개수를 실험할 수 있습니다. 값을 바꾼 뒤 python -m main을 다시 실행하세요.

RAG data ingestion
1. (자동) 메인 앱 실행 시 위 메모리 모듈이 알아서 conversations/messages/message_chunks/chunk_embeddings 테이블을 채웁니다.
2. (수동) 별도 스크립트에서 MemoryStore.create_conversation 등을 호출해 메타데이터를 구성할 수 있습니다.
3. MemoryStore.save_with_embedding(conv_id, role, content)만 호출하면 메시지 원문, 청크, 임베딩이 모두 저장됩니다.
4. chunk_token_size와 chunk_overlap_ratio 인자를 원하는 값으로 지정하거나 환경 변수를 조절해 다양한 구성을 테스트하세요.
