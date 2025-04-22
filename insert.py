# insert.py
# 성경 데이터를 JSON 파일에서 파싱하여 Neo4j에 삽입하는 로직

import json
import logging
from tqdm import tqdm  # 진행률 표시
import graph # graph.py 모듈 임포트

logger = logging.getLogger(__name__)

def insert_bible_data(json_file_path):
    """
    JSON 형식의 성경 파일을 읽어 Neo4j 데이터베이스에 삽입합니다.

    Args:
        json_file_path (str): 성경 데이터 JSON 파일 경로.
                              예상 형식: [{"book": "Genesis", "chapter": 1, "verse": 1, "text": "..."}, ...]
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            bible_data = json.load(f)
        logger.info(f"Successfully loaded {len(bible_data)} verses from {json_file_path}")
    except FileNotFoundError:
        logger.error(f"Error: Bible data file not found at {json_file_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Error: Could not decode JSON from {json_file_path}")
        return
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading the file: {e}")
        return

    # Neo4j 드라이버 가져오기
    driver = graph.get_driver()
    if not driver:
        logger.error("Could not get Neo4j driver. Aborting insertion.")
        return

    inserted_count = 0
    skipped_count = 0

    # tqdm을 사용하여 진행률 표시
    logger.info("Starting data insertion into Neo4j...")
    with driver.session() as session:
        # 성능 향상을 위해 단일 트랜잭션 내에서 여러 작업 수행 고려 가능
        # 여기서는 각 구절별로 MERGE를 사용하여 중복 방지 및 개별 처리
        for verse_data in tqdm(bible_data, desc="Inserting verses"):
            book_name = verse_data.get("book")
            chapter_num = verse_data.get("chapter")
            verse_num = verse_data.get("verse")
            text = verse_data.get("text")

            if not all([book_name, chapter_num, verse_num, text]):
                logger.warning(f"Skipping invalid verse data: {verse_data}")
                skipped_count += 1
                continue

            # Cypher 쿼리: MERGE를 사용하여 노드와 관계 생성 (없으면 생성, 있으면 매칭)
            query = """
            MERGE (b:Book {name: $book_name})
            MERGE (c:Chapter {number: $chapter_num, bookName: $book_name}) // 책별 챕터 구분 위해 bookName 추가
            MERGE (v:Verse {number: $verse_num, chapterNumber: $chapter_num, bookName: $book_name}) // 고유 식별자 강화
            ON CREATE SET v.text = $text
            ON MATCH SET v.text = $text // 이미 존재하면 텍스트 업데이트 (선택적)
            MERGE (b)-[:HAS_CHAPTER]->(c)
            MERGE (c)-[:HAS_VERSE]->(v)
            """
            parameters = {
                "book_name": book_name,
                "chapter_num": int(chapter_num),
                "verse_num": int(verse_num),
                "text": text
            }

            try:
                # session.run 대신 session.execute_write 사용 가능 (트랜잭션 관리)
                session.run(query, parameters)
                inserted_count += 1
            except Exception as e:
                logger.error(f"Failed to insert verse {book_name} {chapter_num}:{verse_num}. Error: {e}")
                skipped_count += 1

    logger.info(f"Data insertion complete. Inserted: {inserted_count}, Skipped: {skipped_count}")

# 사용 예시 (main.py 에서 호출)
# if __name__ == '__main__':
#     # 테스트용 JSON 파일 경로
#     test_json_path = 'path/to/your/bible.json'
#     insert_bible_data(test_json_path)
#     graph.close_driver() # 테스트 완료 후 드라이버 닫기
