import hmac
import hashlib
import re
import requests
from urllib.parse import unquote
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

import json
from html import escape
from automatic import brief
from ai_brief import explain
from providers import Official, demo, DataError
from storage import Store

load_dotenv()
st.set_page_config(page_title="Stock Dash · 퀀트 보드", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
# Streamlit root-level secrets become env vars, but explicit loading is clearer.
try:
    for key in ["APP_PASSWORD", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "DATA_GO_KR_SERVICE_KEY", "DART_CRTFC_KEY", "OPENAI_API_KEY", "OPENAI_MODEL"]:
        if key in st.secrets:
            os.environ[key] = str(st.secrets[key])
except FileNotFoundError:
    pass

st.markdown("""
<style>
:root { --bg:#071326; --panel:#0c1b31; --panel2:#10213b; --line:#203655; --text:#edf4ff; --muted:#8294b2; --green:#19d6a1; --blue:#4d8dff; --purple:#9b70ff; --red:#ff647c; }
.stApp { background: radial-gradient(circle at 70% -10%, #122b50 0, #071326 42%, #06101f 100%); color:var(--text); }
.block-container { max-width: 1700px; padding-top: 1.5rem; padding-bottom: 3rem; }
h1,h2,h3 { letter-spacing:-.04em; color:var(--text); }
.stMarkdown, .stCaption, p, label { color:var(--text); }
div[data-testid="stMetric"] { background:linear-gradient(145deg,#0d1d34,#0a1729); border:1px solid var(--line); border-radius:14px; padding:12px 16px; box-shadow:0 8px 24px #0003; }
div[data-testid="stMetricLabel"] { color:var(--muted); }
div[data-testid="stMetricValue"] { color:var(--text); }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#081529,#06101f); border-right:1px solid #1c304c; }
section[data-testid="stSidebar"] .stButton button { border:0; background:transparent; text-align:left; }
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { color:#91a4c2; }
.stTabs [aria-selected="true"] { color:#fff; }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
.dashboard-title { font-size:2.15rem; font-weight:750; margin: .2rem 0 .1rem; }
.dashboard-subtitle { color:#8da0bd; margin-bottom:1.1rem; }
.dashboard-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:20px 0 16px; }
.d-card { background:linear-gradient(145deg,#17283e,#101e31); border:1px solid #29415d; border-radius:14px; padding:20px; min-height:128px; box-shadow:0 8px 28px #0002; display:flex; align-items:flex-start; gap:18px; }
.d-icon { flex:none; width:54px; height:54px; border-radius:12px; display:grid; place-items:center; background:linear-gradient(140deg,#244f86,#173656); color:#64adff; font-size:1.65rem; }
.d-card:nth-child(2) .d-icon { color:#34dccb; background:linear-gradient(140deg,#155b63,#153849); }
.d-content { min-width:0; }
.d-label { color:#8294b2; font-size:.82rem; }
.d-value { color:#f5f8ff; font-size:1.55rem; font-weight:750; margin:8px 0; }
.d-up { color:var(--green); font-weight:650; }
.d-blue { color:#5da0ff; font-weight:650; }
.d-purple { color:#a77bff; font-weight:650; }
.section-card { background:linear-gradient(145deg,#17283e,#101e31); border:1px solid #29415d; border-radius:14px; padding:22px; min-height:300px; margin-bottom:16px; }
.section-card h3 { margin:0 0 8px; font-size:1.15rem; }
.section-card .hint { color:#8da0bd; font-size:.88rem; }
.empty-chart { height:205px; margin-top:20px; display:flex; align-items:center; justify-content:center; text-align:center; color:#a4b5ce; border:1px solid #29415d; border-radius:10px; background-image:linear-gradient(#273d56 1px,transparent 1px),linear-gradient(90deg,#273d56 1px,transparent 1px); background-size:100% 48px,12.5% 100%; }
.empty-chart span,.empty-donut span { background:#112239e8; border-radius:10px; padding:12px 18px; line-height:1.6; }
.empty-donut { height:225px; display:flex; align-items:center; justify-content:center; flex-direction:column; text-align:center; color:#a4b5ce; }
.donut-outline { width:118px; height:118px; border:2px dashed #6884a5; border-radius:50%; margin-bottom:12px; position:relative; }
.donut-outline:after { content:''; position:absolute; inset:28px; border:1px solid #4b6482; border-radius:50%; }
.watch-row { display:grid; grid-template-columns:2fr 1fr 1fr; gap:12px; padding:13px 0; border-bottom:1px solid #263a52; align-items:center; }
.watch-row:last-child { border-bottom:0; }
.watch-row.head { color:#8da0bd; font-size:.8rem; }
.muted { color:#8da0bd; }
section[data-testid="stSidebar"] { min-width:240px; }
section[data-testid="stSidebar"] h2 { font-size:1.15rem; }
section[data-testid="stSidebar"] .nav-item { display:block; padding:13px 15px; border-radius:10px; color:#bdcce0; text-decoration:none; margin:5px 0; }
section[data-testid="stSidebar"] .nav-item.active { background:#193b68; color:#77baff; border-left:3px solid #4d8dff; }
.analysis-heading { margin:5px 0 12px; padding:16px 20px; background:#152840; border:1px solid #29415d; border-radius:12px; font-size:1.1rem; font-weight:700; }
@media (max-width: 900px) { .dashboard-grid { grid-template-columns:repeat(2,1fr); } .block-container { padding-left:1rem; padding-right:1rem; } }
@media (max-width: 560px) { .dashboard-grid { grid-template-columns:1fr; } .d-card { min-height:110px; } .watch-row { grid-template-columns:1.4fr 1fr .8fr; font-size:.85rem; } }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="dashboard-title">주식 대시보드</div><div class="dashboard-subtitle">시장을 보는 새로운 시선, 더 나은 투자의 시작입니다.</div>', unsafe_allow_html=True)

password = os.getenv("APP_PASSWORD", "")
if password and not st.session_state.get("authorized"):
    with st.form("login"):
        entered = st.text_input("나의 대시보드 비밀번호", type="password")
        if st.form_submit_button("열기"):
            if hmac.compare_digest(entered.encode(), password.encode()):
                st.session_state.authorized = True
                st.rerun()
            else:
                st.error("비밀번호를 확인하세요.")
    st.stop()

class SessionStore:
    """Explicit opt-in practice storage, isolated to this browser session."""
    cloud = False

    def read(self):
        return st.session_state.setdefault("practice_data", {"stocks": [], "journal": [], "runs": []})

    def save_stock(self, stock):
        data = self.read()
        for index, old in enumerate(data["stocks"]):
            if old["code"] == stock["code"]:
                data["stocks"][index] = {**old, **stock}
                return
        data["stocks"].append(stock)

    def log(self, collection, item):
        self.read()[collection].append(item)

    def change(self, operation):
        operation(self.read())


sample_mode = not password
try:
    if sample_mode or st.session_state.get("practice_mode"):
        store = SessionStore()
    else:
        store = Store()
    state = {"stocks": [], "journal": [], "runs": []} if sample_mode else store.read()
except Exception:
    st.error("비밀번호 확인은 통과했지만, 종목 저장 공간을 열지 못했습니다.")
    url_set = bool(os.getenv("SUPABASE_URL", "").strip())
    key_set = bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip())
    if url_set != key_set:
        st.info("Supabase 주소와 키 중 하나만 설정되어 있습니다. DB를 사용하지 않으려면 Secrets에서 SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY 두 항목을 모두 지우고 앱을 재시작하세요.")
    elif url_set:
        st.info("Supabase 설정이 감지됐습니다. 프로젝트 주소·서버 키·schema.sql 실행 여부를 확인하세요. DB를 사용하지 않으려면 두 Supabase 항목을 모두 지우고 앱을 재시작하세요.")
    else:
        st.info("앱이 실행되는 서버의 저장 파일을 열지 못했습니다. 기존 데이터는 덮어쓰지 않았습니다. 아래 버튼으로 별도의 임시 실습을 시작할 수 있습니다.")
    st.caption("임시 실습은 현재 접속에서만 유지됩니다. 새로고침·로그아웃 시 사라질 수 있으며 기존 저장 자료와 합쳐지지 않습니다.")
    if st.button("저장 연결 없이 임시 실습 시작", type="primary"):
        st.session_state.practice_mode = True
        st.rerun()
    st.stop()

if sample_mode:
    st.info("가상 데이터로 둘러보기 · APP_PASSWORD 설정 후 개인 종목 저장과 실데이터 조회가 열립니다.")
elif st.session_state.get("practice_mode"):
    st.warning("임시 실습 · 현재 접속에서만 저장됩니다. 중요한 판단은 개인 문서에 복사해 두세요.")
else:
    st.caption("클라우드 저장 · 다른 기기에서도 이어 사용" if store.cloud else "실행 서버에 저장 · 웹 호스팅 재시작 시 사라질 수 있습니다.")


def run_analysis(code):
    try:
        with st.spinner("공식 시세 · 최근 결산 · 과거 평가 · 사업 공시를 확인합니다…"):
            provider = st.session_state.get("directory_provider") or Official()
            if code.startswith("pending-"):
                pending = next((s for s in state["stocks"] if s["code"] == code), {})
                matches = provider.search(pending.get("name", ""))
                if len(matches) != 1:
                    st.session_state.search_candidates = matches
                    st.info("이름을 정확히 확인하려면 검색 목록에서 종목을 선택하세요.")
                    return
                code = matches[0]["code"]
            price, price_day, price_name = provider.price(code, date.today())
            try:
                report = provider.automatic(code)
            except DataError as error:
                existing = next((s for s in state["stocks"] if s["code"] == code), {})
                partial = {**existing,"code":code,"name":price_name,"kind":existing.get("kind","관심"),
                           "price_snapshot":{"price":price,"date":price_day},"analysis_error":str(error)}
                st.session_state.latest_analysis = partial
                try:
                    store.save_stock(partial)
                    st.session_state.save_notice = "시세·관심종목은 저장했습니다. 재무 분석은 완료되지 않았습니다."
                except Exception:
                    st.session_state.save_notice = "시세만 조회했습니다. 저장소에도 기록하지 못했습니다."
                st.session_state.selected_code=code
                st.session_state.pop("stock_picker",None)
                st.session_state.pop("search_candidates",None)
                st.rerun()
            result = brief(report)
            ai = explain(report, result)
            at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
            existing = next((s for s in state["stocks"] if s["code"] == code), {})
            stock = {**existing, "code": code, "name": report["name"], "kind": existing.get("kind", "관심"),
                     "year": report["years"][-1]["year"], "report": report,
                     "automatic_brief": result, "ai_brief": ai, "analyzed_at": at,"analysis_error":None}
            # Display completed analysis even when a subsequent DB write fails.
            st.session_state.latest_analysis = stock
            try:
                store.save_stock(stock)
                store.log("journal", {"code": code, "at": at, "kind": "automatic",
                                      "report": report, "automatic_brief": result, "ai_brief": ai})
                def consolidate(data):
                    pending_ids = {s["code"] for s in data["stocks"] if s["code"].startswith("pending-") and s["name"].casefold()==report["name"].casefold()}
                    for item in data["journal"]:
                        if item["code"] in pending_ids:
                            item["code"] = code
                    data["stocks"] = [s for s in data["stocks"] if s["code"] not in pending_ids]
                store.change(consolidate)
                st.session_state.save_notice = "분석 결과와 이력을 저장했습니다."
            except Exception:
                st.session_state.save_notice = "분석은 끝났지만 저장하지 못했습니다. 아래 JSON 다운로드로 결과를 보관하세요."
            st.session_state.selected_code = code
            st.session_state.pop("stock_picker", None)
            st.session_state.pop("search_candidates", None)
        st.rerun()
    except DataError as error:
        st.error(str(error))
    except Exception:
        st.error("분석을 마치지 못했습니다. 이전 결과는 유지됩니다. 잠시 후 다시 시도하세요.")


if not sample_mode:
    with st.form("search"):
        query = st.text_input("종목명 또는 키워드", placeholder="삼성전자 · 삼성 · 하이닉스 · 005930")
        submitted = st.form_submit_button("검색·자동 분석", type="primary")
    if submitted:
        try:
            provider = st.session_state.get("directory_provider") or Official()
            st.session_state.directory_provider = provider
            matches = provider.search(query)
            st.session_state.search_candidates = matches
            if len(matches) == 1:
                run_analysis(matches[0]["code"])
            elif not matches:
                st.info("일치하는 상장 기업명이 없습니다. 이름 일부나 6자리 종목코드로 다시 검색하세요.")
        except DataError as error:
            st.error(str(error))
    matches = st.session_state.get("search_candidates", [])
    if len(matches) > 1:
        st.caption("이름에 검색어가 포함된 기업입니다. 종목을 선택하면 코드는 자동으로 입력됩니다.")
        with st.form("candidate"):
            candidate = st.selectbox("검색된 종목", matches, format_func=lambda x: x["name"]+" · "+x["code"])
            if st.form_submit_button("이 종목 분석", type="primary"):
                run_analysis(candidate["code"])

choices = {s["code"]: s for s in state["stocks"]}
latest = st.session_state.get("latest_analysis")
if latest:
    choices[latest["code"]] = latest
with st.sidebar:
    st.header("▥ 투자노트")
    st.caption("더 나은 오늘의 투자")
    st.markdown('<a class="nav-item active" href="#dashboard-overview">⌂ &nbsp;대시보드</a><a class="nav-item" href="#selected-stock-analysis">▥ &nbsp;종목 분석</a><a class="nav-item" href="#watchlist">☆ &nbsp;관심종목</a>', unsafe_allow_html=True)
    st.divider()
    st.subheader("내 분석 기록")
    st.caption("앱 버전 · 연결 진단 01")
    if not sample_mode:
        with st.expander("API 연결 상태 확인"):
            st.caption("현재 앱 서버에서 확인합니다. 키·개인 자료는 결과에 표시하지 않습니다.")
            if st.button("연결 진단 실행"):
                checks = []
                dart_key = os.getenv("DART_CRTFC_KEY", "").strip()
                price_key = unquote(os.getenv("DATA_GO_KR_SERVICE_KEY", "").strip())
                targets = [
                    ("DART 소형 JSON", "https://opendart.fss.or.kr/api/company.json",
                     {"crtfc_key":dart_key,"corp_code":"00126380"}, bool(dart_key)),
                    ("주식시세 JSON", "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo",
                     {"serviceKey":price_key,"resultType":"json","numOfRows":1}, bool(price_key)),
                ]
                for name, url, params, configured in targets:
                    if not configured:
                        checks.append({"항목":name,"결과":"키 설정 없음"})
                        continue
                    try:
                        response = requests.get(url,params=params,timeout=(5,12))
                        if response.status_code != 200:
                            result = "HTTP "+str(response.status_code)
                        else:
                            payload=response.json()
                            code=str(payload.get("status", "")) if name.startswith("DART") else str(payload.get("response",{}).get("header",{}).get("resultCode",""))
                            known={"000":"연결·인증 정상", "00":"연결·인증 정상", "0":"연결·인증 정상",
                                   "010":"DART 키 미등록", "011":"DART 키 중지", "012":"DART IP 제한",
                                   "020":"DART 한도 초과", "013":"연결됨 · 자료 없음", "800":"DART 점검 중"}
                            result=known.get(code,"서버 응답 수신 · 인증 또는 응답 형식 확인 필요")
                        checks.append({"항목":name,"결과":result})
                    except requests.Timeout:
                        checks.append({"항목":name,"결과":"시간 초과 · 인증 판정 불가"})
                    except requests.exceptions.SSLError:
                        checks.append({"항목":name,"결과":"TLS 보안 연결 실패"})
                    except requests.ConnectionError:
                        checks.append({"항목":name,"결과":"연결 실패 · 네트워크/DNS 확인"})
                    except (requests.RequestException,ValueError):
                        checks.append({"항목":name,"결과":"정상 JSON을 받지 못함"})
                st.session_state.connection_checks=checks
            if st.session_state.get("connection_checks"):
                st.dataframe(st.session_state.connection_checks,hide_index=True)
                st.caption("DART JSON도 시간 초과면 기업목록 크기만의 문제로 볼 수 없습니다. JSON이 정상이고 기업목록만 실패하면 다운로드 경로를 점검해야 합니다.")
    if not sample_mode:
        with st.form("save_watch_only"):
            watch_name = st.text_input("관심종목 이름", placeholder="분석 연결이 안 돼도 저장할 수 있습니다")
            watch_code = st.text_input("종목코드 · 알면 입력, 생략 가능", max_chars=6)
            if st.form_submit_button("관심종목 추가"):
                name, code = watch_name.strip(), watch_code.strip()
                if not name or (code and (len(code)!=6 or not code.isascii() or not code.isdigit())):
                    st.error("이름을 입력하고, 코드는 생략하거나 숫자 6자리로 입력하세요.")
                else:
                    existing = next((s for s in state["stocks"] if s["name"].casefold()==name.casefold()), {})
                    identity = existing.get("code") or code or "pending-"+hashlib.sha256(name.casefold().encode()).hexdigest()[:16]
                    try:
                        store.save_stock({"code":identity,"name":name,"kind":existing.get("kind","관심")})
                        st.session_state.selected_code=identity
                        st.session_state.pop("stock_picker",None)
                        st.rerun()
                    except Exception:
                        st.error("관심종목을 저장하지 못했습니다. 저장소 연결을 확인하세요.")
    if choices:
        codes = list(choices)
        preferred = st.session_state.get("selected_code")
        selected = st.selectbox("종목 선택", codes, index=codes.index(preferred) if preferred in codes else 0,
                                format_func=lambda c: choices[c]["name"]+" · "+("코드 확인 대기" if c.startswith("pending-") else c), key="stock_picker")
        stock = choices[selected]
    else:
        stock = {"code": "SAMPLE", "name": "가상 반도체", "report": demo()}
    if password and st.button("로그아웃"):
        st.session_state.clear()
        st.rerun()

report = stock.get("report")
is_demo = stock["code"] == "SAMPLE"

# --- Dashboard overview; portfolio figures require holdings data that this app does not store. ---
if report:
    result_preview = brief(report)
    fair_preview = result_preview.get("fair")
    growth_preview = result_preview.get("growth", "보류")
    value_preview = result_preview.get("value", "보류")
    current_price = report.get("price")
    cards = [("총 자산", "—", "보유 수량 데이터 없음", "d-blue"),
             ("오늘 수익", "—", "매입가·보유 수량 데이터 없음", "d-up"),
             ("선택 종목 기준 종가", f"₩{current_price:,.0f}" if current_price is not None else "—", "가상 예시" if is_demo else str(report.get("price_date", "공식 일별 시세")), "d-blue"),
             ("관심종목", str(len(choices)) if not is_demo else "0", "저장된 종목 수", "d-purple")]
else:
    cards = [("총 자산", "—", "보유 수량 데이터 없음", "d-blue"),
             ("오늘 수익", "—", "매입가·보유 수량 데이터 없음", "d-up"),
             ("선택 종목 기준 종가", "—", "종목 분석 후 표시", "d-blue"),
             ("관심종목", str(len(choices)), "저장된 종목 수", "d-purple")]

st.markdown(
    '<div id="dashboard-overview"></div>' +
    '<div class="dashboard-grid">' +
    ''.join(f'<div class="d-card"><div class="d-icon">{icon}</div><div class="d-content"><div class="d-label">{escape(label)}</div><div class="d-value">{escape(value)}</div><div class="{cls}">{escape(sub)}</div></div></div>' for icon,(label,value,sub,cls) in zip(['▣','▥','⌁','☆'],cards)) +
    '</div>',
    unsafe_allow_html=True
)

left, right = st.columns([1.7, 1], gap="medium")
with left:
    st.markdown('<div class="section-card"><h3>⌁ 포트폴리오 자산 추이</h3><div class="hint">기간별 자산 변화를 확인하세요.</div><div class="empty-chart"><span>보유 종목을 등록하면<br>자산 추이가 표시됩니다.</span></div></div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="section-card"><h3>◉ 자산 구성 현황</h3><div class="hint">종목별 투자 비중</div><div class="empty-donut"><div class="donut-outline"></div><span>보유 수량을 등록하면<br>자산 구성이 표시됩니다.</span></div></div>', unsafe_allow_html=True)

watch_html = '<div id="watchlist" class="section-card"><h3>★ 관심종목</h3><div class="hint">저장된 종목의 마지막 분석 시세 · 실시간 가격이 아닙니다.</div><div class="watch-row head"><span>종목명</span><span>기준 종가</span><span>구분</span></div>'
for item in list(choices.values())[:8]:
    name = escape(str(item.get("name", "")))
    code = str(item.get("code", ""))
    shown_code = escape(code if not code.startswith("pending-") else "코드 확인 대기")
    snapshot = item.get("price_snapshot") or {}
    price = snapshot.get("price") or (item.get("report") or {}).get("price")
    price_text = f'₩{price:,.0f}' if isinstance(price, (int, float)) else '—'
    watch_html += f'<div class="watch-row"><span>{name} <small class="muted">{shown_code}</small></span><span>{price_text}</span><span class="d-blue">{escape(str(item.get("kind", "관심")))}</span></div>'
if not choices or (is_demo and sample_mode):
    watch_html += '<p class="muted">저장된 관심종목이 없습니다. 종목을 검색해 분석해 보세요.</p>'
watch_html += '</div>'
left, right = st.columns([1.7, 1], gap="medium")
with left:
    st.markdown(watch_html, unsafe_allow_html=True)
with right:
    st.markdown('<div class="section-card"><h3>▤ 투자 뉴스</h3><div class="hint">시장 소식</div><div class="empty-donut"><div class="donut-outline"></div><span>뉴스 데이터 연결 대기<br>최근 기사가 연결되면 표시됩니다.</span></div></div>', unsafe_allow_html=True)

st.markdown('<div id="selected-stock-analysis" class="analysis-heading">▥ 선택 종목 분석 &nbsp; '+escape(stock["name"])+( " · 가상 예시" if is_demo else " · "+("코드 확인 대기" if stock["code"].startswith("pending-") else escape(stock["code"])))+'</div>', unsafe_allow_html=True)
if not is_demo:
    if st.button("최신 데이터로 다시 분석"):
        run_analysis(stock["code"])
    if st.session_state.get("save_notice"):
        st.caption(st.session_state.save_notice)

overview, business, journal = st.tabs(["한눈에 분석", "기업·섹터", "분석 기록·투자일지"])
with overview:
    st.subheader("이 종목을 먼저 이해하기")
    if report:
        company=report.get("company",{})
        sectors=brief(report)["sectors"]
        left,right=st.columns([2,1])
        with left:
            st.markdown("**주요 사업 · 공시에서 확인한 특징**")
            excerpt=report.get("business_excerpt","")
            sentences=[x.strip() for x in re.split(r"(?<=[.!?])\s+",excerpt) if 35<len(x.strip())<650 and any(w in x for w in ['사업','제조','생산','판매','서비스']) and re.search(r"다[.!?]$",x.strip()) and '---' not in x]
            if sentences:
                for sentence in sentences[:3]:st.write("• "+sentence)
            elif excerpt:st.info("사업 원문은 수집됐지만 요약할 설명 문장을 찾지 못했습니다. 기업·섹터 탭에서 원문을 확인하세요.")
            else:st.info("사업 원문이 아직 수집되지 않았습니다. 자료가 들어오면 기업 특징을 표시합니다.")
            st.caption("사업보고서 발췌 · "+str(report["years"][-1]["year"])+"년 결산 기준")
        with right:
            st.markdown("**사업 관련 키워드**")
            st.write(" · ".join(x["sector"] for x in sectors) if sectors else "키워드 분류 대기")
            st.caption("원문에 등장한 키워드이며 주력 섹터 확정은 아닙니다.")
            st.write("업종코드: "+str(company.get("induty_code","미수집")))
        st.subheader("최근 공시 · 무엇이 달라졌나요?")
        st.caption("공시 목록 수집일: "+report.get("fetched","")+" · 최근 90일 중 조회된 공시입니다. 실시간 뉴스 전체를 뜻하지 않습니다.")
        notices=sorted(report.get("disclosures",[]),key=lambda x:x.get("date",""),reverse=True)
        if notices:
            for item in notices[:6]:
                st.link_button(item["date"]+" · "+item["title"],item["url"])
        else:st.info("수집본에 최근 공시가 없습니다. 공시가 없다는 확정 판단은 아닙니다.")
        st.markdown("**다음에 확인할 질문**")
        if sectors:
            st.write(" · ".join(sectors[0]["signals"])+"의 변화가 매출과 영업이익에 반영됐나요?")
        else:st.write("매출 증가가 영업이익 증가로 이어졌나요? 최근 공시가 기존 투자 이유를 바꾸나요?")
        ai=stock.get("ai_brief")
        if ai and ai.get("status")=="ok":
            with st.expander("AI 핵심 해설 보기"):st.markdown(ai["text"])
    else:
        st.info("현재 이 종목의 기업·재무 공시 자료가 없습니다. 관심종목 저장과 일지는 사용할 수 있으며, 미수집 정보를 임의로 채우지 않습니다.")
    if stock.get("analysis_error"):
        st.warning(stock["analysis_error"])
        snapshot=stock.get("price_snapshot")
        if snapshot:
            st.metric("조회된 기준 종가",f"{snapshot['price']:,.0f}원")
            st.caption("시세 기준일: "+snapshot["date"])
        if report:
            st.info("아래 재무 분석은 이전에 저장한 결과입니다. 이번 조회로 갱신되지 않았습니다.")
    if not report:
        st.info("관심종목과 투자일지는 사용할 수 있습니다. DART 연결 전에는 성장·적정주가·재무 분석값을 만들지 않습니다.")
    else:
        result = brief(report)
        fair = result["fair"]
        st.caption(f"시세 {report['price_date']} · 결산 {report['years'][-1]['year']} · {report['basis']} · 조회 {report['fetched']}")
        if report.get("sample"):
            st.warning("가상 종목·숫자입니다. 실제 분석은 위 검색창에서 시작하세요.")
        st.write(result["summary"])
        cols = st.columns(4)
        cols[0].metric("기준 종가", f"{report['price']:,.0f}원")
        cols[1].metric("성장", result["growth"])
        cols[2].metric("가치 판단", result["value"])
        cols[3].metric("적정주가 참고값", f"{fair['base']:,.0f}원" if fair else "계산 자료 부족")
        st.subheader("자동 퀀트 진단")
        for col, (name, value), limit in zip(st.columns(3), result["scores"].items(), [30,30,40]):
            col.metric(name, f"{value}/{limit}" if value is not None else "보류")
        st.caption(f"자동 진단 {result['total']}/100 · 규칙 기반 참고 점수" if result["total"] is not None else "계산에 필요한 자료가 없는 항목은 점수를 만들지 않습니다.")
        st.subheader("실적은 성장하고 있나요?")
        chart = pd.DataFrame(report["years"])[["year","revenue","profit"]].rename(columns={"year":"연도","revenue":"매출","profit":"영업이익"})
        chart["연도"] = chart["연도"].astype(str)
        st.bar_chart(chart.set_index("연도"), color=["#b8872e","#65866f"])
        st.dataframe(chart, hide_index=True)
        st.caption("단위 억원 · 확정 결산 3개년. 분기 실적이나 올해 전망을 대신하지 않습니다.")
        st.subheader("현재 가격은 낮은 편인가요?")
        if fair:
            for col, name, key in zip(st.columns(3), ["과거 낮은 배수 적용","과거 중간 배수 적용","과거 높은 배수 적용"], ["low","base","high"]):
                col.metric(name, f"{fair[key]:,.0f}원")
            st.write(f"중간 참고값 대비 가격 차이: {fair['gap']:+.1f}%")
        st.write(result["fair_reason"])
        with st.expander("계산 근거와 한계 확인"):
            st.write("이전 두 결산의 공시일 7일 후까지 조회되는 종가와 시가총액을 이용합니다. 각 시가총액 ÷ 해당 결산 영업이익 배수를 최근 결산 영업이익에 곱하고 현재 상장주식수로 나눕니다.")
            st.write("참고값은 내재가치 확정값·목표주가·미래 이익 예측이 아닙니다. 차입금 변화, 우선주, 비지배지분, 사업구조 변화와 경기 사이클을 충분히 반영하지 못합니다. 과거 저점 이익은 높은 배수를 만들 수 있습니다. 금융업은 계산을 보류합니다.")
            if report.get("anchors"):
                st.dataframe(report["anchors"], hide_index=True)
            st.write("성장 30점: 매출·이익 증가율 규칙. 수익성 30점: 영업이익률 25%에서 만점. 가치 40점: 참고가와 같으면 20점, 가격 차이 ±40%에서 0~40점. 검증된 수익 예측 점수가 아닙니다.")
        for warning in report.get("warnings", []):
            st.caption(warning)
        for row in report["years"]:
            if row.get("url"):
                st.link_button(f"{row['year']}년 공시 원문",row["url"])

with business:
    if report:
        result = brief(report)
        st.subheader("기업 핵심 분석")
        st.write(result["summary"])
        company = report.get("company", {})
        if company:
            st.caption("DART 기업명: "+str(company.get("corp_name",""))+" · 업종코드: "+str(company.get("induty_code","")))
        ai = stock.get("ai_brief")
        if ai and ai.get("status") == "ok":
            st.markdown(ai["text"])
            st.caption("AI 해설 · "+ai["model"]+" · 공시 발췌 기반, 원문 대조 필요")
        elif ai and ai.get("status") == "failed":
            st.info("AI 해설 조회는 실패했습니다. 공식 숫자와 원문은 아래에서 확인할 수 있습니다.")
        else:
            st.caption("현재는 공식 숫자의 규칙 기반 해설입니다. AI 문장 해설은 운영자가 OPENAI_API_KEY와 OPENAI_MODEL을 연결하면 분석할 때 함께 생성됩니다.")
        st.subheader("사업 원문과 섹터 점검")
        excerpt = report.get("business_excerpt","")
        if excerpt:
            st.write(excerpt[:1800]+"…")
            with st.expander("사업보고서 발췌 더 보기"):
                st.text(excerpt)
        else:
            st.info("사업 원문 발췌가 없습니다. 공시 원문을 확인하세요.")
        sectors = result["sectors"]
        if sectors:
            st.caption("공시 발췌의 키워드로 찾은 사업 관련 후보입니다. 공식 업종 분류·주력 사업 확정·최신 섹터 동향 분석은 아닙니다.")
            for sector in sectors:
                with st.container(border=True):
                    st.markdown("**"+sector["sector"]+"**")
                    st.write(sector["logic"])
                    st.write("확인할 지표: "+" · ".join(sector["signals"]))
                    st.caption("원문 발견 단어: "+", ".join(sector["keywords"]))
        else:
            st.write("이 기업의 섹터 분류는 보류합니다. 수요 변화 → 판매량·가격 → 매출 → 영업이익 순서로 공시를 확인하세요.")
        for item in report.get("disclosures",[])[:10]:
            st.link_button(item["date"]+" · "+item["title"],item["url"])

with journal:
    if not is_demo:
        with st.form("note"):
            kind = st.selectbox("내 종목 구분",["관심","보유"],index=1 if stock.get("kind")=="보유" else 0)
            note = st.text_area("나의 판단 · 다음에 확인할 조건")
            if st.form_submit_button("기록 저장"):
                try:
                    store.save_stock({"code":stock["code"],"kind":kind})
                    store.log("journal",{"code":stock["code"],"at":datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),"kind":"note","note":note})
                    st.session_state.pop("latest_analysis",None)
                    st.rerun()
                except Exception:
                    st.error("기록 저장 실패. 입력 내용을 복사해 보관하세요.")
        st.download_button("현재 분석 JSON 다운로드",json.dumps(stock,ensure_ascii=False,indent=2),file_name=stock["code"]+"-analysis.json",mime="application/json")
        history = [item for item in state["journal"] if item["code"]==stock["code"]]
        for item in reversed(history):
            with st.expander(item["at"]+" · "+item["kind"]):
                if item.get("note"):
                    st.write(item["note"])
                elif item.get("automatic_brief"):
                    st.write(item["automatic_brief"]["summary"])
                    st.caption("시세 기준일: "+item.get("report",{}).get("price_date",""))
                with st.expander("저장 원본"):
                    st.json(item)
    else:
        st.info("종목을 분석하면 결과가 자동 저장됩니다. 나의 판단만 한 문장 덧붙이세요.")
