import re
import json
import sys


def parse_bible(input_path: str, output_path: str):
    """
    텍스트 형식의 성경 파일을 파싱하여 JSON 리스트로 저장합니다.

    각 구절은 다음 형태의 JSON 오브젝트로 변환됩니다:
    {
      "book": "창",
      "chapter": 1,
      "verse": 1,
      "text": "태초에 하나님이 천지를 창조하시니라"
    }
    """
    verses = []
    # 패턴: 책줄임 이름 + 장:절, 선택적 제목(<...>), 구절 텍스트
    pattern = re.compile(r'^([^\d]+)(\d+):(\d+)\s*(?:<[^>]+>\s*)?(.*)$')

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if match:
                book = match.group(1)
                chapter = int(match.group(2))
                verse_num = int(match.group(3))
                text = match.group(4)
                verses.append({
                    "book": book,
                    "chapter": chapter,
                    "verse": verse_num,
                    "text": text
                })
            else:
                # 이전 구절의 텍스트가 여러 줄에 걸친 경우 합치기
                if verses:
                    verses[-1]["text"] += ' ' + line

    # JSON 파일로 저장
    with open(output_path, 'w', encoding='utf-8') as out:
        json.dump(verses, out, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("사용법: python parse_bible_to_json.py input.txt output.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    parse_bible(input_file, output_file)
    print(f"파싱 완료: {output_file} 생성됨")