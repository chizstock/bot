"""
한국투자증권 Open API + 기술적 분석 유틸리티
브리핑 크론에서 공통으로 사용
"""
import urllib.request, json, datetime, statistics, time, re

# === CONFIG ===
APP_KEY = "PSD89j5E7i3rYwQqrRaoE5chP4YA8yeEQewY"
APP_SECRET = "6U8bRmNtV7gQ4HRvz3L73zx0JswbpiEf/JAQvfPuwiB9PbWFnbJW9RmnP9g3D6y+x0LtGZxstS7sBF7lDBbxzgdK+Yu6BjypVXLQlVj0B8AD5OR2epIXcsmCC/ojMHvHOhb2rp6tt0M5WxemGxeCodXMwS1eMGKzYDsQ/fZD2NBMUuB2fP0="
BASE_URL = "https://openapi.koreainvestment.com:9443"

PORTFOLIO = {
    '034020': {'name': '두산에너빌리티', 'qty': 416, 'avg': 100441},
    '005930': {'name': '삼성전자', 'qty': 151, 'avg': 200301},
    '247540': {'name': '에코프로비엠', 'qty': 27, 'avg': 308555},
    '138080': {'name': '오이솔루션', 'qty': 115, 'avg': 17591},
    '086790': {'name': '하나금융지주', 'qty': 70, 'avg': 117657},
    '064350': {'name': '현대로템', 'qty': 33, 'avg': 166600},
    '005380': {'name': '현대차', 'qty': 10, 'avg': 516500},
    '105560': {'name': 'KB금융', 'qty': 101, 'avg': 157692},
    '003550': {'name': 'LG(지주)', 'qty': 51, 'avg': 98625},
    '001120': {'name': 'LX인터내셔널', 'qty': 480, 'avg': 41401},
    '005490': {'name': 'POSCO홀딩스', 'qty': 15, 'avg': 543800},
    '000660': {'name': 'SK하이닉스', 'qty': 30, 'avg': 984583},
}

TELEGRAM_TOKEN = "8632142968:AAEeQCAYbnh4-AqcReJClDAeQD5x8y6l8gA"
TELEGRAM_CHAT_ID = 6006891840

# === AUTH ===
_token_cache = {"token": None, "expires": 0}
TOKEN_FILE = "C:\\Users\\신민철/.verdent\\workspace\\base/memories/kis_token.json"

def _load_token_from_file():
    """파일에서 토큰 로드"""
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            return data.get("token"), data.get("expires", 0)
    except:
        return None, 0

def _save_token_to_file(token, expires):
    """토큰을 파일에 저장"""
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump({"token": token, "expires": expires}, f)
    except:
        pass

def get_token():
    """토큰 발급 (파일 캐싱 + 메모리 캐싱)"""
    now = time.time()
    
    # 1. 메모리 캐시 확인
    if _token_cache["token"] and now < _token_cache["expires"]:
        return _token_cache["token"]
    
    # 2. 파일 캐시 확인
    file_token, file_expires = _load_token_from_file()
    if file_token and now < file_expires:
        _token_cache["token"] = file_token
        _token_cache["expires"] = file_expires
        return file_token
    
    # 3. 새 토큰 발급
    url = f"{BASE_URL}/oauth2/tokenP"
    body = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    
    token = result["access_token"]
    expires = now + 80000  # ~22시간
    
    # 캐시 저장
    _token_cache["token"] = token
    _token_cache["expires"] = expires
    _save_token_to_file(token, expires)
    
    return token

def _headers(tr_id):
    token = get_token()
    return {
        "Content-Type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id
    }

def _get(url, tr_id, params):
    req = urllib.request.Request(url + "?" + params, headers=_headers(tr_id))
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

# === GLOBAL MARKET DATA (esignal.co.kr with Selenium) ===
def get_kospi200_futures_esignal():
    """
    esignal.co.kr에서 Selenium으로 JavaScript 렌더링 후 코스피200 야간선물 데이터 추출
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        driver = None
        
        # Chrome 옵션 설정 (헤드리스 모드)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # ChromeDriver 설정
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 페이지 로드
        url = 'https://www.esignal.co.kr/kospi200-futures-night/'
        driver.get(url)
        
        # JavaScript 렌더링 대기
        wait = WebDriverWait(driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
        except:
            pass
        
        time.sleep(5)
        
        # 텍스트 추출
        text = driver.find_element(By.TAG_NAME, 'body').text
        
        result = {
            'source': 'esignal.co.kr (selenium)',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 종가 추출: "970.95 (-9.00, -0.92%)" 패턴
        price_match = re.search(r'(\d{3,4}\.\d{2})\s*\(([\-\+]?\d+\.\d+),\s*([\-\+]?\d+\.\d+)%\)', text)
        if price_match:
            result['price'] = float(price_match.group(1))
            result['change'] = float(price_match.group(2))
            result['change_pct'] = float(price_match.group(3))
        
        # 시가/고가/저가 추출
        ohl_match = re.search(r'시가\s*고가\s*저가\s*([\d.]+)\s*([\d.]+)\s*([\d.]+)', text)
        if ohl_match:
            result['open'] = float(ohl_match.group(1))
            result['high'] = float(ohl_match.group(2))
            result['low'] = float(ohl_match.group(3))
        
        # 주간 종가/거래량 추출
        day_close_match = re.search(r'주간\s*종가\s*거래량\s*갱신\s*시간\s*([\d.]+)\s*([\d,]+)', text)
        if day_close_match:
            result['day_close'] = float(day_close_match.group(1))
            result['volume'] = int(day_close_match.group(2).replace(',', ''))
        
        # 1차/2차 목표가 추출
        target_match = re.search(r'1차목표:\s*([\d.]+)\s*2차목표:\s*([\d.]+)', text)
        if target_match:
            result['target_1'] = float(target_match.group(1))
            result['target_2'] = float(target_match.group(2))
        
        # 주간 종가 대비 갭 계산
        if 'price' in result and 'day_close' in result:
            result['gap'] = round(result['price'] - result['day_close'], 2)
            result['gap_pct'] = round((result['gap'] / result['day_close']) * 100, 2)
        
        driver.quit()
        return result if 'price' in result else {'error': 'parse failed'}
        
    except Exception as e:
        if 'driver' in locals() and driver:
            driver.quit()
        return {'error': str(e)}

def get_kospi200_futures():
    """
    코스피200 선물 데이터 수집 (우선순위: esignal selenum > 한투 > 기타)
    """
    # 1. esignal selenum 시도 (JavaScript 렌더링)
    esignal_data = get_kospi200_futures_esignal()
    if 'error' not in esignal_data:
        return esignal_data
    
    # 2. 한투 API 시도
    try:
        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-futuresprice"
        params = "FID_COND_MRKT_DIV_CODE=JF&FID_INPUT_ISCD=101V06&FID_INPUT_DATE_1=&FID_INPUT_DATE_2="
        result = _get(url, "FHKST130100C0", params)
        output = result.get("output", [])
        if output:
            latest = output[0]
            return {
                'price': float(latest.get('futs_prpr', 0)),
                'change': float(latest.get('futs_prdy_vrss', 0)),
                'change_pct': float(latest.get('futs_prdy_ctrt', 0)),
                'volume': int(latest.get('futs_acml_vol', 0)),
                'source': 'kis_api'
            }
    except:
        pass
    
    # 3. 실패 시 에러 반환
    return {'error': 'all sources failed', 'esignal_error': esignal_data.get('error')}

# === STOCK PRICE DATA ===
def get_price_naver(code):
    """네이버 실시간 시세 (rate limit 없음, 빠름)"""
    try:
        url = f'https://m.stock.naver.com/api/stock/{code}/basic'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req)
        d = json.loads(resp.read().decode())
        return {
            'code': code,
            'name': d.get('stockName', ''),
            'price': int(d.get('closePrice', '0').replace(',', '')),
            'change': int(d.get('compareToPreviousClosePrice', '0').replace(',', '')),
            'change_pct': float(d.get('fluctuationsRatio', 0)),
            'open': int(d.get('openPrice', '0').replace(',', '')),
            'high': int(d.get('highPrice', '0').replace(',', '')),
            'low': int(d.get('lowPrice', '0').replace(',', '')),
            'volume': int(d.get('accumulatedTradingVolume', 0)),
            'foreign_ratio': float(d.get('foreignOwnershipRatio', 0)),
        }
    except Exception as e:
        return {'code': code, 'error': str(e)}

def get_price_kis(code):
    """한투 실시간 시세 (정확도 높음, rate limit 있음)"""
    try:
        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
        params = f"FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD={code}"
        result = _get(url, "FHKST01010100", params)
        d = result.get("output", {})
        return {
            'code': code,
            'price': int(d.get('stck_prpr', 0)),
            'change': int(d.get('prdy_vrss', 0)),
            'change_pct': float(d.get('prdy_ctrt', 0)),
            'open': int(d.get('stck_oprc', 0)),
            'high': int(d.get('stck_hgpr', 0)),
            'low': int(d.get('stck_lwpr', 0)),
            'volume': int(d.get('acml_vol', 0)),
            'foreign_ratio': float(d.get('hts_frgn_ehrt', 0)),
            'per': float(d.get('per', 0)),
            'pbr': float(d.get('pbr', 0)),
        }
    except Exception as e:
        return {'code': code, 'error': str(e)}

def get_price(code, source='naver'):
    """통합 시세 조회 (기본: 네이버, 정확도 필요시: kis)"""
    if source == 'kis':
        return get_price_kis(code)
    return get_price_naver(code)

def get_daily_chart(code, start_date, end_date):
    """일봉 차트 데이터 (최대 100건/호출)"""
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    params = (f"FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD={code}"
              f"&FID_INPUT_DATE_1={start_date}&FID_INPUT_DATE_2={end_date}"
              f"&FID_PERIOD_DIV_CODE=D&FID_ORG_ADJ_PRC=0")
    return _get(url, "FHKST03010100", params).get("output2", [])

def get_daily_chart_naver(code, page=1, page_size=60):
    """네이버 일봉 차트 (rate limit 없음)"""
    try:
        url = f'https://m.stock.naver.com/api/stock/{code}/price?pageSize={page_size}&page={page}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req)
        items = json.loads(resp.read().decode())
        # 네이버 형식을 한투 형식으로 변환 (쉼표 제거)
        result = []
        for item in items:
            result.append({
                'stck_bsop_date': item['localTradedAt'].replace('-', ''),
                'stck_oprc': item['openPrice'].replace(',', ''),
                'stck_hgpr': item['highPrice'].replace(',', ''),
                'stck_lwpr': item['lowPrice'].replace(',', ''),
                'stck_clpr': item['closePrice'].replace(',', ''),
                'acml_vol': str(item['accumulatedTradingVolume'])
            })
        return result
    except Exception as e:
        return []

def get_daily_chart_long_naver(code, days=500):
    """네이버 장기 일봉 데이터"""
    all_data = []
    page = 1
    while len(all_data) < days:
        items = get_daily_chart_naver(code, page=page, page_size=60)
        if not items:
            break
        all_data.extend(items)
        page += 1
        time.sleep(0.1)
    return all_data[:days]

def get_daily_chart_long(code, days=500, source='naver'):
    """장기 일봉 데이터 (기본: 네이버, 한투는 fallback)"""
    if source == 'naver':
        return get_daily_chart_long_naver(code, days)
    # 한투 API (정확도 높음)
    all_data = []
    end = datetime.date.today()
    while len(all_data) < days:
        start = end - datetime.timedelta(days=120)
        items = get_daily_chart(code, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
        if not items:
            break
        all_data.extend(items)
        last_date = items[-1].get("stck_bsop_date", "")
        if last_date:
            end = datetime.datetime.strptime(last_date, "%Y%m%d").date() - datetime.timedelta(days=1)
        else:
            break
        time.sleep(0.5)
    return all_data[:days]

def get_investor(code):
    """투자자별 매매동향"""
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"
    params = f"FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD={code}"
    return _get(url, "FHKST01010900", params).get("output", [])

def get_volume_rank():
    """거래량 순위"""
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/volume-rank"
    params = ("FID_COND_MRKT_DIV_CODE=J&FID_COND_SCR_DIV_CODE=20171&FID_INPUT_ISCD=0000"
              "&FID_DIV_CLS_CODE=0&FID_BLNG_CLS_CODE=0&FID_TRGT_CLS_CODE=111111111"
              "&FID_TRGT_EXLS_CLS_CODE=000000&FID_INPUT_PRICE_1=0&FID_INPUT_PRICE_2=0"
              "&FID_VOL_CNT=0&FID_INPUT_DATE_1=")
    return _get(url, "FHKST130000C0", params).get("output", [])

# === TECHNICAL ANALYSIS ===
def calc_technical(code, days=500, source='naver'):
    """종목의 기술적 지표 전체 계산 (기본: 네이버)"""
    data = get_daily_chart_long(code, days, source=source)
    if len(data) < 56:
        return None

    closes = [int(d['stck_clpr']) for d in data]
    highs = [int(d['stck_hgpr']) for d in data]
    lows = [int(d['stck_lwpr']) for d in data]
    volumes = [int(d['acml_vol']) for d in data]
    opens = [int(d['stck_oprc']) for d in data]

    result = {"price": closes[0], "data_days": len(data)}

    # Moving Averages
    for period in [5, 20, 33, 56, 112, 224, 448]:
        if len(closes) >= period:
            result[f"ma{period}"] = sum(closes[:period]) / period

    # Golden Cross checks
    if "ma56" in result and "ma33" in result:
        result["gc_56_33"] = result["ma56"] > result["ma33"]
    if "ma112" in result and "ma56" in result:
        result["gc_112_56"] = result["ma112"] > result["ma56"]

    # MA Arrangement
    if all(f"ma{p}" in result for p in [112, 224, 448]):
        m112, m224, m448 = result["ma112"], result["ma224"], result["ma448"]
        if m112 > m224 > m448:
            result["ma_arrangement"] = "BULLISH"
        elif m112 < m224 < m448:
            result["ma_arrangement"] = "BEARISH"
        else:
            result["ma_arrangement"] = "TRANSITIONING"

    # Volume ratio (today vs 20d avg)
    if len(volumes) >= 20:
        vol_avg20 = sum(volumes[:20]) / 20
        result["vol_ratio"] = volumes[0] / vol_avg20 * 100 if vol_avg20 > 0 else 0
        result["vol_today"] = volumes[0]
        result["vol_avg20"] = vol_avg20

    # Bollinger Bands (20d)
    if len(closes) >= 20:
        bb = closes[:20]
        bbm = statistics.mean(bb)
        bbs = statistics.stdev(bb)
        result["bb_upper"] = bbm + 2 * bbs
        result["bb_mid"] = bbm
        result["bb_lower"] = bbm - 2 * bbs
        # BB width (squeeze detection)
        result["bb_width"] = (result["bb_upper"] - result["bb_lower"]) / bbm * 100

    # Ichimoku Cloud
    if len(data) >= 52:
        tenkan = (max(highs[:9]) + min(lows[:9])) / 2
        kijun = (max(highs[:26]) + min(lows[:26])) / 2
        senkou_a = (tenkan + kijun) / 2
        senkou_b = (max(highs[:52]) + min(lows[:52])) / 2
        cloud_top = max(senkou_a, senkou_b)
        cloud_bottom = min(senkou_a, senkou_b)
        result["ichimoku"] = {
            "tenkan": tenkan, "kijun": kijun,
            "senkou_a": senkou_a, "senkou_b": senkou_b,
            "cloud_top": cloud_top, "cloud_bottom": cloud_bottom
        }
        if closes[0] > cloud_top:
            result["cloud_position"] = "ABOVE"
        elif closes[0] < cloud_bottom:
            result["cloud_position"] = "BELOW"
        else:
            result["cloud_position"] = "INSIDE"

    # Candle pattern detection (세력봉/매집봉 근사)
    if len(data) >= 20:
        body_ratio = abs(closes[0] - opens[0]) / max(highs[0] - lows[0], 1)
        is_bullish = closes[0] > opens[0]
        vol_spike = result.get("vol_ratio", 0) > 200
        result["power_candle"] = is_bullish and body_ratio > 0.7 and vol_spike

    # 224일선 대비 위치
    if "ma224" in result:
        result["above_ma224"] = closes[0] > result["ma224"]
        result["ma224_dist"] = (closes[0] - result["ma224"]) / result["ma224"] * 100

    return result

# === DANTE STRATEGY SCORING ===
def dante_score(ta):
    """단테 밥그릇 3번 자리 점수 (필수 6 + 우대 4)"""
    if ta is None:
        return 0, 0, []

    mandatory = 0
    optional = 0
    reasons = []

    # 필수 1: 이평선 역배열→수렴/정배열 전환
    arr = ta.get("ma_arrangement", "")
    if arr in ("TRANSITIONING", "BULLISH"):
        mandatory += 1
        reasons.append(f"이평선 {arr}")

    # 필수 2: 구름대 위 안착
    if ta.get("cloud_position") == "ABOVE":
        mandatory += 1
        reasons.append("구름대 위 안착")

    # 필수 3: 224일선 돌파/근접
    if ta.get("above_ma224"):
        mandatory += 1
        reasons.append(f"224일선 돌파 ({ta.get('ma224_dist',0):.1f}%)")
    elif ta.get("ma224_dist", -999) > -3:
        mandatory += 1
        reasons.append(f"224일선 근접 ({ta.get('ma224_dist',0):.1f}%)")

    # 필수 4: 거래량 150%+
    if ta.get("vol_ratio", 0) >= 150:
        mandatory += 1
        reasons.append(f"거래량 {ta.get('vol_ratio',0):.0f}%")

    # 필수 5: 골든크로스
    if ta.get("gc_56_33") or ta.get("gc_112_56"):
        mandatory += 1
        gc_type = "56>33" if ta.get("gc_56_33") else "112>56"
        reasons.append(f"GC {gc_type}")

    # 필수 6: 세력봉
    if ta.get("power_candle"):
        mandatory += 1
        reasons.append("세력봉 감지")

    # 우대 1: 볼밴 수렴 후 상단 돌파
    if ta.get("bb_width", 999) < 10 and ta.get("price", 0) > ta.get("bb_upper", 999999):
        optional += 1
        reasons.append("볼밴 수렴 돌파")

    # 우대 2: 구름대 상방 전환
    ichi = ta.get("ichimoku", {})
    if ichi.get("senkou_a", 0) > ichi.get("senkou_b", 0):
        optional += 1
        reasons.append("구름대 상방")

    return mandatory, optional, reasons

# === TELEGRAM ===
def send_telegram(text):
    data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

def send_telegram_long(text):
    while text:
        send_telegram(text[:4096])
        text = text[4096:]
        if text:
            time.sleep(0.5)

# === PORTFOLIO ANALYSIS ===
def analyze_portfolio(source='naver'):
    """포트폴리오 전 종목 실시간 분석 (네이버 기본, 한투 보조)"""
    results = []
    for code, info in PORTFOLIO.items():
        try:
            # 1. 시세 조회 (네이버 or 한투)
            price_data = get_price(code, source=source)
            if 'error' in price_data:
                raise Exception(price_data['error'])
            
            cur_price = price_data['price']
            pnl_pct = (cur_price - info["avg"]) / info["avg"] * 100
            pnl_amt = (cur_price - info["avg"]) * info["qty"]
            
            # 2. 투자자동향은 한투 API로 (정확도 높음, 종목당 1회)
            time.sleep(0.3)
            try:
                investor_data = get_investor(code)
                foreign_buy = int(investor_data[0].get("frgn_ntby_qty", 0)) if investor_data else 0
                inst_buy = int(investor_data[0].get("orgn_ntby_qty", 0)) if investor_data else 0
            except:
                foreign_buy = 0
                inst_buy = 0
            
            results.append({
                "code": code,
                "name": info["name"],
                "qty": info["qty"],
                "avg": info["avg"],
                "cur_price": cur_price,
                "change_pct": price_data.get('change_pct', 0),
                "pnl_pct": pnl_pct,
                "pnl_amt": pnl_amt,
                "foreign_net": foreign_buy,
                "inst_net": inst_buy,
                "volume": price_data.get('volume', 0),
                "foreign_ratio": price_data.get('foreign_ratio', 0),
            })
            time.sleep(0.1)  # rate limit 방지
        except Exception as e:
            results.append({"code": code, "name": info["name"], "error": str(e)})
    return results

if __name__ == "__main__":
    print("=== KIS Utility Test ===")
    token = get_token()
    print(f"Token OK")

    print("\n--- Portfolio ---")
    portfolio = analyze_portfolio()
    for p in portfolio:
        if "error" in p:
            print(f"  {p['name']}: ERROR {p['error']}")
        else:
            print(f"  {p['name']}: {p['cur_price']:,} ({p['change_pct']:+.2f}%) | PnL: {p['pnl_pct']:+.1f}% | Foreign: {p['foreign_net']:+,}")

    print("\n--- Technical Analysis (Samsung) ---")
    ta = calc_technical("005930", 500)
    if ta:
        for k, v in ta.items():
            if k != "ichimoku":
                print(f"  {k}: {v}")
        m, o, reasons = dante_score(ta)
        print(f"\n  Dante Score: mandatory={m}/6, optional={o}/4")
        print(f"  Reasons: {', '.join(reasons)}")
