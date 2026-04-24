"""
GenSpark AI Plus - 쿠키 기반 로그인 자동화

사용 방법:
1. Chrome에서 https://www.genspark.ai 접속
2. 로그인 후 AI 채팅 페이지로 이동
3. 개발자 도구(F12) → Application → Cookies → genspark.ai
4. 쿠키 값을 복사하여 아래 COOKIES 딕셔너리에 저장
5. 또는 export_cookies_from_chrome() 함수로 자동 추출
"""
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# === 쿠키 저장 파일 ===
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "genspark_cookies.json")


class GenSparkChat:
    """GenSpark AI Plus AI 채팅 (쿠키 기반 로그인)"""
    
    def __init__(self, headless=True, timeout=60):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.chat_url = "https://www.genspark.ai/agents?type=ai_chat"
        self.session_active = False
        
    def _init_driver(self):
        """Chrome 드라이버 초기화"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''Object.defineProperty(navigator, 'webdriver', {get: () => undefined})'''
        })
        
    def _load_cookies(self):
        """저장된 쿠키 로드"""
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
        
    def _save_cookies(self, cookies):
        """쿠키 저장"""
        with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
            
    def start_chat(self):
        """AI 채팅 세션 시작 (쿠키 기반)"""
        if not self.driver:
            self._init_driver()
            
        # 먼저 기본 페이지 로드 (쿠키 적용을 위해 동일 도메인 필요)
        self.driver.get("https://www.genspark.ai")
        time.sleep(2)
        
        # 저장된 쿠키 로드 및 적용
        cookies = self._load_cookies()
        if cookies:
            for cookie in cookies:
                try:
                    # 쿠키 도메인 처리
                    if 'domain' in cookie:
                        cookie['domain'] = '.genspark.ai'
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    pass
            time.sleep(1)
            
        # AI 채팅 페이지로 이동
        self.driver.get(self.chat_url)
        time.sleep(5)
        
        # 로그인 상태 확인
        if not self._check_login():
            print("로그인 필요: 쿠키가 만료되었거나 없습니다.")
            print(f"쿠키 파일 위치: {COOKIE_FILE}")
            return self._manual_login_guide()
            
        self.session_active = True
        return self
        
    def _check_login(self):
        """로그인 상태 확인"""
        try:
            # 로그인된 상태에서만 보이는 요소 확인
            # 예: 사용자 프로필, 로그아웃 버튼, 채팅 입력창 등
            indicators = [
                "//textarea",  # 채팅 입력창
                "//div[contains(@class, 'chat')]",  # 채팅 영역
                "//button[contains(text(), 'Send') or contains(text(), '전송')]",  # 전송 버튼
            ]
            
            for indicator in indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                if elements:
                    return True
                    
            # URL 확인
            if "/chat" in self.driver.current_url:
                return True
                
        except:
            pass
            
        return False
        
    def _manual_login_guide(self):
        """수동 로그인 가이드"""
        guide = """
=== GenSpark AI 로그인 필요 ===

1. PC에서 Chrome 브라우저를 열고 https://www.genspark.ai 에 접속하세요.

2. 로그인하세요 (이메일/비밀번호 또는 소셜 로그인)

3. AI 채팅 페이지로 이동하세요

4. 개발자 도구 열기 (F12)

5. Application → Cookies → https://www.genspark.ai 선택

6. 모든 쿠키를 복사하여 아래 파일에 저장하세요:
   {cookie_file}

   형식:
   [
     {{"name": "session_id", "value": "...", "domain": ".genspark.ai"}},
     {{"name": "auth_token", "value": "...", "domain": ".genspark.ai"}}
   ]

7. 다시 시도하세요.
""".format(cookie_file=COOKIE_FILE)
        
        print(guide)
        return None
        
    def send(self, message, wait_for_response=True, response_timeout=60):
        """AI 채팅에 메시지 전송"""
        if not self.session_active:
            result = self.start_chat()
            if result is None:
                return "로그인이 필요합니다. 위 가이드를 따라주세요."

        # JavaScript로 입력 (더 유연한 방식)
        try:
            # 먼저 입력창 찾기 - 더 많은 선택자 시도
            input_found = self.driver.execute_script("""
                const selectors = [
                    'textarea[placeholder*="무엇을"]', 
                    'textarea[placeholder*="도와"]', 
                    'textarea',
                    'input[placeholder*="무엇을"]',
                    'input[placeholder*="도와"]',
                    'div[contenteditable="true"]',
                    '[role="textbox"]',
                    'input[type="text"]'
                ];
                for (let sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) {
                        // 요소가 화면에 보이는지 확인
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            return {found: true, selector: sel, tag: el.tagName};
                        }
                    }
                }
                // placeholder 텍스트로 찾기
                const allInputs = document.querySelectorAll('textarea, input, div[contenteditable]');
                for (let el of allInputs) {
                    const placeholder = el.getAttribute('placeholder') || '';
                    if (placeholder.includes('무엇') || placeholder.includes('도와') || placeholder.includes('message')) {
                        return {found: true, selector: 'placeholder', tag: el.tagName};
                    }
                }
                return {found: false};
            """)

            if not input_found.get('found'):
                # 페이지 스크린샷 저장 (디버깅용)
                try:
                    self.driver.save_screenshot("genspark_debug.png")
                    print("스크린샷 저장: genspark_debug.png")
                except:
                    pass
                return "입력창을 찾을 수 없습니다. 페이지 구조를 확인해주세요."

            # JavaScript로 값 설정
            self.driver.execute_script("""
                const selectors = [
                    'textarea[placeholder*="무엇을"]',
                    'textarea[placeholder*="도와"]',
                    'textarea',
                    'input[placeholder*="무엇을"]',
                    'input[placeholder*="도와"]',
                    'div[contenteditable="true"]',
                    'input[type="text"]'
                ];
                let inputEl = null;
                for (let sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) {
                        inputEl = el;
                        break;
                    }
                }
                
                if (!inputEl) {
                    // 모든 input/textarea 중에서 가장 아래쪽에 있는 것 선택
                    const allInputs = Array.from(document.querySelectorAll('textarea, input[type="text"], div[contenteditable]'));
                    const visibleInputs = allInputs.filter(el => el.offsetParent !== null);
                    if (visibleInputs.length > 0) {
                        inputEl = visibleInputs[visibleInputs.length - 1]; // 마지막(보통 채팅 입력창)
                    }
                }
                
                if (inputEl) {
                    inputEl.focus();
                    if (inputEl.isContentEditable || inputEl.getAttribute('contenteditable') === 'true') {
                        inputEl.innerText = arguments[0];
                    } else {
                        inputEl.value = arguments[0];
                    }
                    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
                    inputEl.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                return false;
            """, message)

            time.sleep(0.8)

            # Enter 키 전송
            self.driver.execute_script("""
                const selectors = [
                    'textarea[placeholder*="무엇을"]',
                    'textarea[placeholder*="도와"]',
                    'textarea',
                    'input[placeholder*="무엇을"]',
                    'input[placeholder*="도와"]',
                    'div[contenteditable="true"]',
                    'input[type="text"]'
                ];
                let inputEl = null;
                for (let sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) {
                        inputEl = el;
                        break;
                    }
                }
                
                if (!inputEl) {
                    const allInputs = Array.from(document.querySelectorAll('textarea, input[type="text"], div[contenteditable]'));
                    const visibleInputs = allInputs.filter(el => el.offsetParent !== null);
                    if (visibleInputs.length > 0) {
                        inputEl = visibleInputs[visibleInputs.length - 1];
                    }
                }
                
                if (inputEl) {
                    inputEl.dispatchEvent(new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        cancelable: true
                    }));
                    inputEl.dispatchEvent(new KeyboardEvent('keyup', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true
                    }));
                }
            """)

            time.sleep(0.5)

        except Exception as e:
            return f"입력 오류: {e}"

        if not wait_for_response:
            return None

        return self._wait_for_response(response_timeout)
        
    def _wait_for_response(self, timeout=60):
        """AI 응답 대기"""
        start_time = time.time()
        last_response = ""
        
        print("응답 대기 중...", end="", flush=True)
        
        while time.time() - start_time < timeout:
            try:
                # 페이지에서 긴 텍스트 찾기
                texts = self.driver.execute_script("""
                    const divs = Array.from(document.querySelectorAll('div, article, section'));
                    return divs
                        .map(el => el.innerText)
                        .filter(text => text && text.length > 200)
                        .sort((a, b) => b.length - a.length);
                """)
                
                if texts and len(texts[0]) > len(last_response):
                    last_response = texts[0]
                    
                # 안정화 확인
                if len(last_response) > 300:
                    time.sleep(2)
                    new_texts = self.driver.execute_script("""
                        const divs = Array.from(document.querySelectorAll('div, article, section'));
                        return divs.map(el => el.innerText).filter(text => text && text.length > 200);
                    """)
                    if new_texts and new_texts[0] == last_response:
                        print(f" 완료 ({len(last_response)}자)")
                        return last_response
                        
            except:
                pass
                
            print(".", end="", flush=True)
            time.sleep(1)
            
        print(f" 시간초과 ({len(last_response)}자)")
        return last_response if last_response else "응답을 받지 못했습니다."
        
    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.session_active = False
            
    def __enter__(self):
        self.start_chat()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# === 편의 함수 ===

def ask_genspark(message, mode="pro", headless=True):
    """GenSpark AI에 간단하게 질문"""
    with GenSparkChat(headless=headless) as chat:
        if chat.session_active:
            return chat.send(message)
        return "로그인이 필요합니다."

def analyze_stock_genspark(stock_name, stock_code=None):
    """주식 분석"""
    code_str = f"({stock_code})" if stock_code else ""
    prompt = f"""{stock_name}{code_str} 종목을 분석해주세요.

다음 내용을 포함해주세요:
1. 기업 개요 및 사업 모델
2. 최근 실적 및 재무 상태
3. 투자 포인트 및 리스크
4. 투자 의견 (단기/중기)

한국어로 작성해주세요."""
    
    return ask_genspark(prompt)

def summarize_genspark(text, max_length=500):
    """텍스트 요약"""
    prompt = f"""다음 내용을 {max_length}자 이내로 요약해주세요:

{text}

요약 형식:
📌 핵심 요약
• 주요 포인트
💡 시장 영향"""
    
    return ask_genspark(prompt)


def export_cookies_from_chrome():
    """
    Chrome에서 쿠키 추출 가이드
    (사용자가 직접 실행해야 함)
    """
    guide = f"""
=== Chrome 쿠키 추출 방법 ===

1. Chrome에서 https://www.genspark.ai 접속

2. 로그인 (이메일/비밀번호 또는 소셜 로그인)

3. AI 채팅 페이지로 이동

4. F12 (개발자 도구) → Console 탭

5. 아래 코드 붙여넣기:

   copy(JSON.stringify(document.cookie.split('; ').map(c => {{
     const [name, value] = c.split('=');
     return {{name, value, domain: '.genspark.ai'}};
   }}), null, 2))

6. 클립보드에 복사된 내용을 아래 파일에 저장:
   {COOKIE_FILE}

7. 저장 후 다시 시도하세요.
"""
    
    print(guide)
    return guide


if __name__ == "__main__":
    # 테스트
    print("GenSpark AI Chat 모듈")
    print("-" * 50)
    
    # 쿠키 파일 확인
    if not os.path.exists(COOKIE_FILE):
        print("쿠키 파일이 없습니다. 로그인 가이드를 출력합니다.")
        export_cookies_from_chrome()
    else:
        print("쿠키 파일 발견. 테스트를 시작합니다.")
        result = ask_genspark("안녕하세요")
        print("응답:", result[:500] if len(str(result)) > 500 else result)
