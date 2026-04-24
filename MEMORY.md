# Memory

## User Profile
- 이름: 신민철
- 호칭: 베르 (Manager nickname)
- 관심사: 주식 투자, 시장 분석

## Preferences
- 언어: 한국어
- 평일(월~금) 아침 7:30 주식시장 브리핑 크론 (id: loop_4d6c121988bd)
- 텔레그램 채팅으로 아침 알람 수신
  - Bot: @Chizver_bot
  - Token: 8779182520:AAEoZIuzrwmkbLjjTMwK_nZvh9-5VT4Z5lU
  - Chat ID: 6006891840
  - 기본 모드: ECO (경량 응답)
  - 모드 전환: "자동모드", "일반모드", "풀모드" 키워드 사용 시 일반 모드로 전환
  - 자동 복귀: 일반 모드 응답 후 자동으로 ECO 모드로 복귀
- GenSpark AI Plus 연동
  - 파일: memories/genspark_ai.py
  - 기능: 주식 분석, 뉴스 요약, 데이터 해석
  - 사용: `ask_genspark(prompt)`, `analyze_with_genspark(name, code)`, `summarize_with_genspark(text)`
- 한국투자증권 Open API 연동
  - App Key: PSD89j5E7i3rYwQqrRaoE5chP4YA8yeEQewY
  - App Secret: 6U8bRmNtV7gQ4HRvz3L73zx0JswbpiEf/JAQvfPuwiB9PbWFnbJW9RmnP9g3D6y+x0LtGZxstS7sBF7lDBbxzgdK+Yu6BjypVXLQlVj0B8AD5OR2epIXcsmCC/ojMHvHOhb2rp6tt0M5WxemGxeCodXMwS1eMGKzYDsQ/fZD2NBMUuB2fP0=
  - 계좌: 7343287901
  - Base URL: https://openapi.koreainvestment.com:9443

## Portfolio
> 포트폴리오 변경 시 "포트폴리오 변경 : [종목] [수량] [매수/매도]" 형식으로 입력하면 아래 내용 자동 반영

| 종목 | 수량 | 평균매수가 | 비고 |
|------|------|-----------|------|
| 두산에너빌리티 | 416주 | 100,441 | |
| 삼성전자 | 151주 | 200,301 | |
| 에코프로비엠 | 27주 | 308,555 | |
| 오이솔루션 | 115주 | 17,591 | |
| 하나금융지주 | 70주 | 117,657 | |
| 현대로템 | 33주 | 166,600 | |
| 현대차 | 10주 | 516,500 | |
| KB금융 | 101주 | 157,692 | |
| LG(지주) | 51주 | 98,625 | |
| LX인터내셔널 | 480주 | 41,401 | |
| POSCO홀딩스 | 15주 | 543,800 | |
| SK하이닉스 | 30주 | 984,583 | |

## Portfolio Rules
- 사용자가 "포트폴리오 변경" 키워드로 입력 시 즉시 MEMORY.md 포트폴리오 테이블 업데이트
- 포트폴리오는 사용자가 변경할 때까지 영구 유지

## Portfolio Opinion Rules
- 수익률 % 기반 기계적 매도/보유 판단 사용 금지
- AI가 아래 정보를 종합하여 자체적으로 의견 판단:
  1. 해당 종목 관련 최신 뉴스/이슈 (실적, 수주, 규제, 산업 동향 등)
  2. 코스피/코스닥 지수 흐름 및 수급 동향 (외국인/기관)
  3. 섹터별 강약, 글로벌 매크로 (환율, 유가, 미국 증시 등)
  4. 기술적 분석 (이평선 배열, 거래량, 추세)
  5. 투자자동향 (외국인/기관 순매수/순매도)
- 의견 유형: 보유 / 추가매수 / 부분매도 / 전량매도
  - 추가매수 시 → 매수추천가(지정가) + 근거
  - 부분매도 시 → 추천매도가 + 보유수량 대비 매도 비중(%) + 근거
  - 전량매도 시 → 추천매도가 + 손절가 + 근거
- 현재가 표시 시 당일 등락폭(%) 반드시 병기
  예: 삼성전자: 220,250원 (▼1.89%) | 수익률 +10.0%
