# main.py
# Click 기반 CLI 애플리케이션 진입점

import click
import logging
import atexit # 애플리케이션 종료 시 정리 작업

# 프로젝트 루트에서 실행될 때 모듈 임포트 경로 설정 (필요시)
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# 로컬 모듈 임포트
import insert, search, faiss_index, graph, config

# 로깅 설정 (graph.py 에서 이미 설정되었을 수 있음, 여기서 레벨 등 조정 가능)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 애플리케이션 종료 시 Neo4j 드라이버 닫기 등록
atexit.register(graph.close_driver)

@click.group()
def cli():
    """Bible Search CLI Tool using FAISS and Neo4j."""
    pass

@cli.command('insert-bible')
@click.argument('json_file_path', type=click.Path(exists=True, dir_okay=False))
def insert_bible_command(json_file_path):
    """
    Parses a JSON Bible file and inserts data into Neo4j.

    JSON_FILE_PATH: Path to the Bible data file in JSON format.
    Expected format: [{"book": "Genesis", "chapter": 1, "verse": 1, "text": "..."}, ...]
    """
    click.echo(f"Starting Bible data insertion from: {json_file_path}")
    try:
        insert.insert_bible_data(json_file_path)
        click.echo("Data insertion process finished.")
    except Exception as e:
        logger.error(f"An error occurred during data insertion: {e}", exc_info=True)
        click.echo(f"Error during insertion: {e}", err=True)

@cli.command('run-search-shell')
def run_search_shell_command():
    """Starts an interactive shell for searching Bible verses."""
    click.echo("Launching interactive search shell...")
    try:
        search.run_search_shell()
    except Exception as e:
        logger.error(f"An error occurred while running the search shell: {e}", exc_info=True)
        click.echo(f"Error in search shell: {e}", err=True)

@cli.command('build-faiss-index')
def build_faiss_index_command():
    """Builds and saves the FAISS index for all verses in Neo4j."""
    click.echo("Starting FAISS index building process...")
    try:
        success = faiss_index.build_and_save_index()
        if success:
            click.echo(f"FAISS index successfully built and saved to {config.FAISS_INDEX_PATH}")
        else:
            click.echo("FAISS index building failed. Check logs for details.", err=True)
    except Exception as e:
        logger.error(f"An error occurred during FAISS index building: {e}", exc_info=True)
        click.echo(f"Error building FAISS index: {e}", err=True)

@cli.command('list-books')
def list_books_command():
    """Lists all Bible books registered in the Neo4j database."""
    click.echo("Listing registered Bible books...")
    try:
        books = graph.list_all_books()
        if books:
            click.echo("Registered Books:")
            for book in books:
                click.echo(f"- {book}")
        else:
            click.echo("No books found in the database.")
    except Exception as e:
        logger.error(f"An error occurred while listing books: {e}", exc_info=True)
        click.echo(f"Error listing books: {e}", err=True)

@cli.command('list-topics')
def list_topics_command():
    """Lists all topics registered in the Neo4j database."""
    # 참고: 이 기능은 Topic 노드가 DB에 존재해야 작동합니다.
    click.echo("Listing registered topics...")
    try:
        topics = graph.list_all_topics()
        if topics:
            click.echo("Registered Topics:")
            for topic in topics:
                click.echo(f"- {topic}")
        else:
            click.echo("No topics found in the database. (Ensure Topic nodes exist)")
    except Exception as e:
        logger.error(f"An error occurred while listing topics: {e}", exc_info=True)
        click.echo(f"Error listing topics: {e}", err=True)

@cli.command('clear-database')
@click.option('--force', is_flag=True, help='Skip confirmation prompt (Use with caution!).')
def clear_database_command(force):
    """
    Clears all nodes and relationships from the Neo4j database.
    Requires confirmation unless --force is used.
    """
    click.echo(click.style("WARNING: This will delete ALL data in the Neo4j database!", fg='red', bold=True))
    confirmed = False
    if force:
        confirmed = True
    else:
        # click.confirm 사용
        if click.confirm("Are you absolutely sure you want to clear the entire database?"):
             confirmed = True

    if confirmed:
        click.echo("Proceeding with database clearing...")
        try:
            success = graph.clear_all_data() # graph.py 함수는 내부적으로 input() 대신 click.confirm 사용하도록 수정 가능
            if success:
                click.echo("Database cleared successfully.")
            else:
                # graph.clear_all_data() 에서 False 반환 시 (사용자 취소 등)
                if not force: # 사용자가 취소한 경우
                     click.echo("Database clear operation cancelled by user.")
                else: # 강제 실행 중 오류 발생 시
                     click.echo("Failed to clear database. Check logs.", err=True)

        except Exception as e:
            logger.error(f"An error occurred while clearing the database: {e}", exc_info=True)
            click.echo(f"Error clearing database: {e}", err=True)
    else:
         # click.confirm 에서 No 선택 시
         click.echo("Database clear operation cancelled.")


if __name__ == '__main__':
    # 모듈로 실행될 때 (__init__.py 필요) 또는 직접 실행될 때
    # 예: python -m your_package_name 또는 python main.py
    cli()
