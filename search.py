# search.py
# 자연어 검색 로직 및 대화형 검색 셸

import numpy as np
import logging
import faiss_index, graph, config # 필요한 모듈 임포트

logger = logging.getLogger(__name__)

def search_similar_verses(query: str, index, model, k: int = config.DEFAULT_SEARCH_RESULTS):
    """
    주어진 자연어 질의에 대해 FAISS 인덱스를 검색하여 가장 유사한 K개의 구절을 찾습니다.

    Args:
        query (str): 사용자 검색어.
        index: 로드된 FAISS 인덱스 객체 (IndexIDMap).
        model: 로드된 Sentence Transformer 모델 객체.
        k (int): 반환할 결과 수.

    Returns:
        list: 유사한 구절 정보 딕셔너리의 리스트. 각 딕셔너리는 Neo4j 노드 ID와 거리를 포함.
              예: [{'node_id': 123, 'distance': 0.5}, ...]
              오류 발생 시 빈 리스트 반환.
    """
    if not query:
        logger.warning("Search query is empty.")
        return []
    if index is None or model is None:
        logger.error("FAISS index or model is not loaded. Cannot perform search.")
        return []

    try:
        logger.info(f"Encoding search query: '{query}'")
        # 쿼리 임베딩 생성 및 FAISS 검색 가능한 형태로 변환
        query_embedding = model.encode([query])[0].astype('float32').reshape(1, -1)

        logger.info(f"Searching FAISS index for {k} nearest neighbors...")
        # FAISS 검색 실행 (거리와 ID 반환)
        distances, ids = index.search(query_embedding, k=k)

        # 결과 처리 (ids[0]에 결과 ID 배열, distances[0]에 거리 배열 포함)
        results = []
        if ids.size > 0 and distances.size > 0:
            for i in range(len(ids[0])):
                node_id = int(ids[0][i]) # IndexIDMap 사용 시 반환된 ID가 Neo4j 노드 ID
                distance = float(distances[0][i])
                # 유효하지 않은 ID (-1) 필터링 (IndexIVF 등에서 발생 가능)
                if node_id != -1:
                    results.append({"node_id": node_id, "distance": distance})
            logger.info(f"Found {len(results)} similar verses in FAISS.")
        else:
            logger.info("No results found in FAISS for the query.")

        return results

    except Exception as e:
        logger.error(f"Error during FAISS search for query '{query}': {e}")
        return []

def get_verse_details_from_neo4j(faiss_results: list):
    """
    FAISS 검색 결과 (Neo4j 노드 ID 리스트)를 기반으로 Neo4j에서 구절 상세 정보를 조회합니다.

    Args:
        faiss_results (list): FAISS 검색 결과 딕셔너리 리스트 [{'node_id': ..., 'distance': ...}, ...].

    Returns:
        list: 각 구절의 상세 정보 (책, 장, 절, 텍스트)와 거리를 포함한 딕셔너리 리스트.
              예: [{'book': 'Genesis', 'chapter': 1, 'verse': 1, 'text': '...', 'distance': 0.5}, ...]
    """
    detailed_results = []
    if not faiss_results:
        return []

    logger.info(f"Fetching details for {len(faiss_results)} verses from Neo4j...")
    # 각 노드 ID에 대해 Neo4j에서 정보 조회
    for result in faiss_results:
        node_id = result.get("node_id")
        distance = result.get("distance")
        if node_id is not None:
            verse_info = graph.get_verse_by_id(node_id) # graph.py의 함수 사용
            if verse_info:
                # graph.get_verse_by_id 반환값은 Record 객체이므로 딕셔너리로 변환
                verse_detail = dict(verse_info) # Record 객체를 딕셔너리로 변환
                verse_detail['distance'] = distance # 검색 거리 추가
                detailed_results.append(verse_detail)
            else:
                logger.warning(f"Could not retrieve details for Neo4j node ID {node_id}")

    logger.info(f"Successfully fetched details for {len(detailed_results)} verses.")
    return detailed_results

def run_search_shell():
    """대화형 검색 셸을 실행합니다."""
    logger.info("Initializing search shell...")

    # FAISS 인덱스와 모델 로드 시도
    index, model = faiss_index.load_faiss_index()
    if index is None or model is None:
        logger.error("Failed to load FAISS index or model. Search shell cannot start.")
        print("Error: Could not load necessary search components. Please build the index first using 'build-faiss-index'.")
        return

    print("\n--- Bible Natural Language Search Shell ---")
    print("Enter your search query (e.g., 'love your neighbor').")
    print("Type 'exit' or 'quit' to leave.")

    while True:
        try:
            query = input("\nSearch> ").strip()

            if query.lower() in ['exit', 'quit']:
                print("Exiting search shell.")
                break

            if not query:
                continue

            # 1. FAISS 유사 구절 검색
            faiss_results = search_similar_verses(query, index, model, k=config.DEFAULT_SEARCH_RESULTS)

            if not faiss_results:
                print("No similar verses found.")
                continue

            # 2. Neo4j에서 상세 정보 조회
            detailed_results = get_verse_details_from_neo4j(faiss_results)

            # 3. 결과 출력
            if detailed_results:
                print("\n--- Search Results ---")
                for i, result in enumerate(detailed_results):
                    print(f"{i+1}. {result['book']} {result['chapter']}:{result['verse']}")
                    print(f"   Text: {result['text']}")
                    print(f"   Similarity Score (Distance): {result['distance']:.4f}") # 거리는 작을수록 유사
                    # TODO: 여기서 추가적인 Graph 탐색 로직 호출 가능 (예: 관련 주제, 인물 찾기)
            else:
                print("Could not retrieve details for the found verses.")

        except KeyboardInterrupt:
            print("\nExiting search shell (Ctrl+C pressed).")
            break
        except Exception as e:
            logger.error(f"An error occurred in the search shell: {e}")
            print(f"An error occurred: {e}")

# 사용 예시 (main.py 에서 호출)
# if __name__ == '__main__':
#     run_search_shell()
#     graph.close_driver() # 셸 종료 후 드라이버 닫기
