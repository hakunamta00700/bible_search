# faiss_index.py
# FAISS 인덱스 생성, 저장, 로딩 및 관련 유틸리티

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
import os
import json
from tqdm import tqdm
import graph, config # graph.py, config.py 모듈 임포트

logger = logging.getLogger(__name__)

# 전역 모델 인스턴스 (메모리에 로드하여 재사용)
_model = None

def get_embedding_model():
    """Sentence Transformer 모델을 로드합니다 (싱글턴 패턴)."""
    global _model
    if _model is None:
        try:
            logger.info(f"Loading sentence transformer model: {config.EMBEDDING_MODEL}")
            _model = SentenceTransformer(config.EMBEDDING_MODEL)
            logger.info("Sentence transformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
    return _model

def build_and_save_index():
    """
    Neo4j에서 모든 구절을 가져와 임베딩을 생성하고 FAISS 인덱스를 빌드하여 저장합니다.
    FAISS 인덱스 ID와 Neo4j 노드 ID 간의 매핑도 저장합니다.
    """
    logger.info("Starting FAISS index building process...")

    # 1. Neo4j에서 데이터 가져오기
    logger.info("Fetching verses from Neo4j...")
    verses_data = graph.get_all_verses_for_indexing()
    if not verses_data:
        logger.warning("No verses found in Neo4j. Cannot build FAISS index.")
        return False

    node_ids, texts = zip(*verses_data)
    logger.info(f"Fetched {len(texts)} verses.")

    # 2. 임베딩 생성
    try:
        model = get_embedding_model()
        logger.info("Generating embeddings for verses...")
        # 배치 처리로 메모리 효율성 및 속도 향상 가능
        embeddings = model.encode(texts, show_progress_bar=True, batch_size=128) # tqdm 진행률 표시
        embeddings = np.array(embeddings).astype('float32') # FAISS는 float32 필요
        logger.info(f"Generated {embeddings.shape[0]} embeddings with dimension {embeddings.shape[1]}.")
    except Exception as e:
        logger.error(f"Error during embedding generation: {e}")
        return False

    # 3. FAISS 인덱스 빌드
    dimension = embeddings.shape[1]
    try:
        # 간단한 IndexFlatL2 사용, 데이터 크기에 따라 다른 인덱스 고려 (e.g., IndexIVFFlat)
        index = faiss.IndexFlatL2(dimension)
        # ID 매핑을 위한 IndexIDMap 추가 (FAISS 결과 인덱스를 원래 Neo4j ID로 매핑)
        # FAISS 인덱스는 0부터 시작하는 정수 ID를 사용하므로, Neo4j의 고유 ID (node_id)를 사용하기 위해 매핑
        index_mapped = faiss.IndexIDMap(index)
        # FAISS에 (임베딩, Neo4j 노드 ID) 쌍 추가
        index_mapped.add_with_ids(embeddings, np.array(node_ids).astype('int64')) # ID는 int64 필요
        logger.info(f"FAISS index built successfully. Total vectors indexed: {index_mapped.ntotal}")
    except Exception as e:
        logger.error(f"Error building FAISS index: {e}")
        return False

    # 4. FAISS 인덱스 저장
    try:
        logger.info(f"Saving FAISS index to {config.FAISS_INDEX_PATH}")
        faiss.write_index(index_mapped, config.FAISS_INDEX_PATH) # IndexIDMap 저장
        logger.info("FAISS index saved successfully.")
    except Exception as e:
        logger.error(f"Error saving FAISS index: {e}")
        return False

    # 5. ID 매핑 저장 (IndexIDMap 사용 시 별도 매핑 파일 불필요)
    # IndexIDMap을 사용하면 FAISS 검색 결과로 나온 ID가 바로 Neo4j 노드 ID가 됩니다.
    # 따라서 별도의 id_map.json 파일은 필요하지 않습니다.
    # 만약 IndexFlatL2만 사용했다면, 여기서 node_ids 리스트를 저장해야 합니다.
    # logger.info(f"Saving ID map to {config.ID_MAP_PATH}")
    # try:
    #     with open(config.ID_MAP_PATH, 'w') as f:
    #         # FAISS 인덱스 (0, 1, 2...) 와 Neo4j node_id 매핑
    #         id_map = {i: node_id for i, node_id in enumerate(node_ids)}
    #         json.dump(id_map, f)
    #     logger.info("ID map saved successfully.")
    # except Exception as e:
    #     logger.error(f"Error saving ID map: {e}")
    #     # 인덱스 저장은 성공했을 수 있으므로 False 반환은 보류
    #     pass

    logger.info("FAISS index building and saving process completed.")
    return True


def load_faiss_index():
    """
    저장된 FAISS 인덱스와 임베딩 모델을 로드합니다.

    Returns:
        tuple: (faiss_index, model) 또는 로딩 실패 시 (None, None)
               faiss_index: 로드된 FAISS 인덱스 객체 (IndexIDMap)
               model: 로드된 Sentence Transformer 모델 객체
    """
    logger.info("Loading FAISS index and model...")
    index = None
    model = None

    # FAISS 인덱스 로드
    if not os.path.exists(config.FAISS_INDEX_PATH):
        logger.error(f"FAISS index file not found at {config.FAISS_INDEX_PATH}. Please build the index first.")
        return None, None
    try:
        logger.info(f"Loading FAISS index from {config.FAISS_INDEX_PATH}")
        index = faiss.read_index(config.FAISS_INDEX_PATH)
        logger.info(f"FAISS index loaded successfully. Index type: {type(index)}, Total vectors: {index.ntotal}")
        # IndexIDMap 인스턴스인지 확인 (선택적)
        if not isinstance(index, faiss.IndexIDMap):
             logger.warning("Loaded index is not an IndexIDMap. ID mapping might be incorrect if not handled properly.")

    except Exception as e:
        logger.error(f"Error loading FAISS index: {e}")
        return None, None

    # 임베딩 모델 로드
    try:
        model = get_embedding_model()
    except Exception as e:
        logger.error(f"Failed to load embedding model during index load: {e}")
        return None, None # 모델 로드 실패 시 인덱스만 반환하지 않음

    logger.info("FAISS index and model loaded successfully.")
    return index, model

# 사용 예시 (main.py 에서 호출)
# if __name__ == '__main__':
#     # 인덱스 빌드 테스트
#     # build_and_save_index()
#
#     # 인덱스 로드 테스트
#     loaded_index, loaded_model = load_faiss_index()
#     if loaded_index and loaded_model:
#         print("Index and model loaded.")
#         # 간단한 검색 테스트
#         query_embedding = loaded_model.encode(["God is love"])[0].astype('float32').reshape(1, -1)
#         distances, ids = loaded_index.search(query_embedding, k=5)
#         print("Search results (Neo4j Node IDs):", ids[0])
#         print("Distances:", distances[0])
#     else:
#         print("Failed to load index or model.")
#
#     graph.close_driver()
