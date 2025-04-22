# Dockerfile for running Neo4j

# 공식 Neo4j 이미지를 기반으로 합니다.
# 특정 버전을 사용하려면 neo4j:5.18.0 과 같이 태그를 지정하세요.
# 최신 안정 버전을 사용하려면 'latest' 또는 특정 버전 시리즈 (예: '5')를 사용할 수 있습니다.
FROM neo4j:5

# 환경 변수 설정
# Neo4j 인증 설정 (사용자명/비밀번호)
# config.py 에 설정된 값과 일치시킵니다. (neo4j/password)
# 보안을 위해 실제 운영 환경에서는 더 강력한 비밀번호를 사용하고,
# Docker secret 이나 다른 보안 메커니즘을 통해 관리하는 것이 좋습니다.
ENV NEO4J_AUTH=neo4j/password

# Neo4j가 사용하는 기본 포트를 노출합니다.
# 7474: Neo4j Browser 및 HTTP API 용
# 7687: Bolt 프로토콜 (드라이버 연결용)
EXPOSE 7474 7687

# (선택 사항) 사용자 정의 설정 파일 복사
# 로컬의 neo4j.conf 파일을 컨테이너의 /conf 디렉토리로 복사할 수 있습니다.
# COPY neo4j.conf /conf/neo4j.conf

# (선택 사항) 플러그인 설치
# APOC과 같은 플러그인을 설치하려면 아래 주석을 해제하고 필요한 플러그인을 추가하세요.
# RUN wget -O /var/lib/neo4j/plugins/apoc.jar "https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/5.x.x/apoc-5.x.x-core.jar"
# RUN echo "dbms.security.procedures.unrestricted=apoc.*" >> /conf/neo4j.conf

# 컨테이너 시작 시 Neo4j 서버 실행 (기본 이미지에 정의되어 있음)
CMD ["neo4j"]
