# 국내·미국 주식 검색

대시보드 상단의 **주식 검색 → 검색 시장**에서 국내 또는 미국을 선택합니다.

- 국내: 삼성전자, 삼성, 005930처럼 이름·이름 일부·6자리 코드를 검색합니다. 기존 시세 조회와 DART 자동 분석으로 이어집니다.
- 미국: Apple, Microsoft, AAPL, TSLA처럼 영문 기업명·티커를 검색합니다. 미국 주식의 기업명·티커·통화를 표로 표시합니다. 미국 현재가·재무 분석·관심종목 저장은 이 검색 기능에 포함되지 않습니다.

## 서버 설정

기존 국내 설정은 유지합니다. 미국 검색은 [Alpha Vantage 키 발급](https://www.alphavantage.co/support/#api-key) 후 실행 서버의 `.env` 또는 Streamlit Secrets에 아래 항목을 추가하세요.

```toml
ALPHAVANTAGE_API_KEY = "발급받은 키"
```

실제 키를 GitHub 코드나 채팅에 입력하지 마세요. GitHub Actions Secrets만 설정하면 Streamlit 앱에는 전달되지 않습니다. [공식 SYMBOL_SEARCH 문서](https://www.alphavantage.co/documentation/#symbolsearch)에 따른 API를 사용하며, 계정의 이용 한도와 접근 권한이 적용됩니다. 검색 결과는 미국 Equity 항목만 표시합니다. 한글 미국 기업명과 ETF 검색은 지원하지 않습니다.

샘플 모드에서도 미국 검색 화면은 열리지만 실제 검색에는 위 키가 필요합니다. 앱 비밀번호가 설정돼 있으면 로그인 후 접근합니다.

## 검증

```bash
python -m unittest test_us_search -v
python -m py_compile app.py us_search.py
```

테스트는 응답 모의 검증입니다. 실제 키를 설정한 서버에서 AAPL 검색을 실행해 연결을 확인하세요.
