"""US equity directory search; no prices or DART analysis are implied."""
import os
import requests


class SearchError(RuntimeError):
    pass


def search_us(query):
    query = query.strip()
    if not query:
        return []
    if len(query) > 100:
        raise SearchError("검색어를 100자 이내로 입력하세요.")
    key = os.getenv("ALPHAVANTAGE_API_KEY", "").strip()
    if not key:
        raise SearchError("미국 종목 검색에는 ALPHAVANTAGE_API_KEY가 필요합니다. 서버 Secrets에 설정하세요.")
    try:
        response = requests.get("https://www.alphavantage.co/query",
                                params={"function": "SYMBOL_SEARCH", "keywords": query, "apikey": key},
                                timeout=(5, 15))
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        raise SearchError("미국 검색 서버에 연결하지 못했습니다. 잠시 후 다시 시도하세요.") from None
    if not isinstance(payload, dict):
        raise SearchError("미국 검색 응답 형식을 확인할 수 없습니다.")
    if payload.get("Note") or payload.get("Information"):
        raise SearchError("미국 검색 API의 이용 한도 또는 접근 권한을 확인하세요.")
    if "Error Message" in payload or not isinstance(payload.get("bestMatches"), list):
        raise SearchError("미국 검색 API 키와 응답 형식을 확인하세요.")
    results = {}
    for row in payload["bestMatches"]:
        if not isinstance(row, dict) or row.get("4. region") != "United States" or row.get("3. type") != "Equity":
            continue
        symbol, name = row.get("1. symbol"), row.get("2. name")
        if not isinstance(symbol, str) or not isinstance(name, str) or not symbol or not name:
            continue
        results[symbol] = {"티커": symbol, "기업명": name, "시장": "미국", "통화": row.get("8. currency", "USD")}
    return list(results.values())


def render_us_search(st):
    st.caption("미국 기업명은 영문 또는 티커로 검색하세요. 예: Apple · AAPL · Microsoft · TSLA")
    st.caption("기업명·티커 검색만 제공합니다. 현재가와 국내 DART 자동 분석은 포함되지 않습니다.")
    with st.form("us_stock_search"):
        query = st.text_input("미국 기업명 또는 티커", max_chars=100)
        submitted = st.form_submit_button("미국 주식 검색", type="primary")
    if submitted:
        st.session_state.pop("us_search_results", None)
        if not query.strip():
            st.info("기업명 또는 티커를 입력하세요.")
        else:
            try:
                with st.spinner("미국 종목을 검색합니다…"):
                    st.session_state.us_search_results = search_us(query)
            except SearchError as error:
                st.error(str(error))
                st.markdown("[Alpha Vantage API 키 발급](https://www.alphavantage.co/support/#api-key)")
    if "us_search_results" in st.session_state:
        results = st.session_state.us_search_results
        if results:
            st.dataframe(results, hide_index=True, use_container_width=True)
        else:
            st.info("일치하는 미국 주식이 없습니다. 영문 기업명 또는 티커로 다시 검색하세요.")
