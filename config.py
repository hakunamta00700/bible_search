# config.py
# 애플리케이션 설정을 관리합니다.

# Neo4j 설정
NEO4J_URI = "bolt://localhost:7687"  # Neo4j 데이터베이스 URI
NEO4J_USER = "neo4j"                # Neo4j 사용자 이름
NEO4J_PASSWORD = "password"         # Neo4j 비밀번호 (실제 환경에서는 보안 강화 필요)

# Sentence Transformer 모델 설정
EMBEDDING_MODEL = 'all-MiniLM-L6-v2' # 사용할 임베딩 모델 이름
# 다국어 지원 시: 'paraphrase-multilingual-MiniLM-L12-v2' 등 고려

# FAISS 설정
FAISS_INDEX_PATH = "faiss.index"     # FAISS 인덱스 파일 저장 경로
ID_MAP_PATH = "id_map.json"          # FAISS 인덱스 ID와 Neo4j 노드 ID 매핑 파일 경로

# 기타
DEFAULT_SEARCH_RESULTS = 5           # 기본 검색 결과 수
