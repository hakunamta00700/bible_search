# graph.py
# Neo4j 데이터베이스 연결 및 유틸리티 함수

import logging
from neo4j import GraphDatabase, basic_auth
import config # config.py 에서 설정 로드

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 전역 드라이버 인스턴스 (애플리케이션 수명 동안 유지)
_driver = None

def get_driver():
    """Neo4j 드라이버 인스턴스를 가져옵니다 (싱글턴 패턴)."""
    global _driver
    if _driver is None:
        try:
            logger.info(f"Connecting to Neo4j at {config.NEO4J_URI}")
            _driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=basic_auth(config.NEO4J_USER, config.NEO4J_PASSWORD)
            )
            _driver.verify_connectivity() # 연결 확인
            logger.info("Successfully connected to Neo4j.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise  # 연결 실패 시 예외 발생
    return _driver

def close_driver():
    """Neo4j 드라이버 연결을 닫습니다."""
    global _driver
    if _driver is not None:
        logger.info("Closing Neo4j driver connection.")
        _driver.close()
        _driver = None

def run_query(query, parameters=None):
    """주어진 Cypher 쿼리를 실행하고 결과를 반환합니다."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(query, parameters)
            # 결과를 리스트로 변환하여 반환 (레코드 객체 포함)
            return [record for record in result]
    except Exception as e:
        logger.error(f"Error executing Cypher query: {query} with params {parameters}. Error: {e}")
        return [] # 오류 발생 시 빈 리스트 반환

def clear_all_data():
    """데이터베이스의 모든 노드와 관계를 삭제합니다."""
    logger.warning("Attempting to clear all data from the database.")
    # 사용자 확인 절차 추가 권장
    confirmation = input("Are you sure you want to delete ALL data? (yes/no): ")
    if confirmation.lower() == 'yes':
        try:
            run_query("MATCH (n) DETACH DELETE n")
            logger.info("Successfully cleared all data from the database.")
            return True
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False
    else:
        logger.info("Database clear operation cancelled.")
        return False

def list_all_books():
    """GraphDB에 등록된 모든 성경 책(Book) 목록을 반환합니다."""
    query = "MATCH (b:Book) RETURN b.name ORDER BY b.name"
    try:
        results = run_query(query)
        return [record["b.name"] for record in results]
    except Exception as e:
        logger.error(f"Failed to list books: {e}")
        return []

def list_all_topics():
    """GraphDB에 등록된 모든 주제(Topic) 목록을 반환합니다."""
    # 참고: Topic 노드와 관련 데이터가 DB에 있어야 함
    query = "MATCH (t:Topic) RETURN t.name ORDER BY t.name"
    try:
        results = run_query(query)
        if not results:
            logger.info("No topics found in the database.")
        return [record["t.name"] for record in results]
    except Exception as e:
        logger.error(f"Failed to list topics: {e}")
        return []

def get_verse_by_id(node_id: int):
    """Neo4j 내부 ID로 구절 정보를 조회합니다."""
    query = """
    MATCH (v:Verse) WHERE id(v) = $node_id
    MATCH (c:Chapter)-[:HAS_VERSE]->(v)
    MATCH (b:Book)-[:HAS_CHAPTER]->(c)
    RETURN b.name AS book, c.number AS chapter, v.number AS verse, v.text AS text
    """
    try:
        result = run_query(query, parameters={"node_id": node_id})
        if result:
            return result[0] # 첫 번째 결과 반환 (단일 노드 조회)
        else:
            logger.warning(f"Verse with node ID {node_id} not found.")
            return None
    except Exception as e:
        logger.error(f"Error fetching verse by ID {node_id}: {e}")
        return None

def get_all_verses_for_indexing():
    """FAISS 인덱싱을 위해 모든 구절의 텍스트와 Neo4j ID를 조회합니다."""
    query = "MATCH (v:Verse) RETURN id(v) AS node_id, v.text AS text"
    try:
        results = run_query(query)
        # 결과가 많을 경우 메모리 관리를 위해 제너레이터 사용 고려
        return [(record["node_id"], record["text"]) for record in results]
    except Exception as e:
        logger.error(f"Failed to fetch all verses for indexing: {e}")
        return []

# 애플리케이션 종료 시 드라이버 닫기 (예: main.py 에서 호출)
# import atexit
# atexit.register(close_driver)
