"""
GenSpark AI Plus - Playwright 기반 연동
주식 분석, 뉴스 요약, 데이터 해석 등에 활용
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

# === 쿠키 저장 파일 ===
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "genspark_cookies.json")


class GenSparkChat:
    """GenSpark AI Plus AI 채팅 (Playwright 기반)"""
    
    def __init__(self, headless=True, timeout=60):
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.page = None
        self.chat_url = "https://www.genspark.ai/agents?type=ai_chat"
        
    async def start_chat(self):
        """AI 채팅 세션 시작"""
        playwright = await async_playwright().start()
        
        # 브라우저 실행
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # 컨텍스트 생성 (쿠키 지원)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # 쿠키 로드
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, 'r') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
        
        # 페이지 생성
        self.page = await self.context.new_page()
        
        # AI 채팅 페이지로 이동
        await self.page.goto(self.chat_url, wait_until='networkidle')
        await asyncio.sleep(5)
        
        # 로그인 상태 확인
        if not await self._check_login():
            print("로그인 필요: 쿠키가 만료되었거나 없습니다.")
            print(f"쿠키 파일 위치: {COOKIE_FILE}")
            await self.close()
            return None
            
        return self
        
    async def _check_login(self):
        """로그인 상태 확인"""
        try:
            # 채팅 입력창이 있는지 확인
            textarea = await self.page.query_selector('textarea')
            if textarea:
                return True
                
            # URL 확인
            if "/agents" in self.page.url:
                return True
                
        except:
            pass
        return False
        
    async def send(self, message, wait_for_response=True, response_timeout=60):
        """AI 채팅에 메시지 전송"""
        if not self.page:
            await self.start_chat()
            if not self.page:
                return "로그인이 필요합니다."
        
        try:
            # 입력창 찾기 및 입력
            textarea = await self.page.wait_for_selector(
                'textarea[placeholder*="무엇이든"], textarea',
                timeout=10000
            )
            
            if not textarea:
                return "입력창을 찾을 수 없습니다."
            
            # 클릭 후 입력
            await textarea.click()
            await textarea.fill(message)
            await asyncio.sleep(0.5)
            
            # Enter 키 전송
            await textarea.press('Enter')
            
        except Exception as e:
            return f"입력 오류: {e}"
        
        if not wait_for_response:
            return None
            
        return await self._wait_for_response(response_timeout)
        
    async def _wait_for_response(self, timeout=60):
        """AI 응답 대기"""
        start_time = asyncio.get_event_loop().time()
        last_response = ""
        
        print("응답 대기 중...", end="", flush=True)
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                # 페이지에서 긴 텍스트 찾기
                texts = await self.page.evaluate("""
                    () => {
                        const divs = Array.from(document.querySelectorAll('div, article, section'));
                        return divs
                            .map(el => el.innerText)
                            .filter(text => text && text.length > 200)
                            .sort((a, b) => b.length - a.length);
                    }
                """)
                
                if texts and len(texts[0]) > len(last_response):
                    last_response = texts[0]
                    
                # 충분한 길이와 안정성 확인
                if len(last_response) > 300:
                    await asyncio.sleep(2)
                    new_texts = await self.page.evaluate("""
                        () => {
                            const divs = Array.from(document.querySelectorAll('div, article, section'));
                            return divs.map(el => el.innerText).filter(text => text && text.length > 200);
                        }
                    """)
                    if new_texts and new_texts[0] == last_response:
                        print(f" 완료 ({len(last_response)}자)")
                        return last_response
                        
            except:
                pass
                
            print(".", end="", flush=True)
            await asyncio.sleep(1)
            
        print(f" 시간초과 ({len(last_response)}자)")
        return last_response if last_response else "응답을 받지 못했습니다."
        
    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
            
    async def __aenter__(self):
        await self.start_chat()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# === 동기 래퍼 함수 ===

def ask_genspark(message, mode="pro", headless=True):
    """GenSpark AI에 간단하게 질문 (동기 함수)"""
    async def _ask():
        async with GenSparkChat(headless=headless) as chat:
            if chat.page:
                return await chat.send(message)
            return "로그인이 필요합니다."
    
    return asyncio.run(_ask())

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


# === kis_utils.py 통합용 ===

def quick_chat(message):
    """kis_utils.py 통합용"""
    return ask_genspark(message)


if __name__ == "__main__":
    # 테스트
    print("GenSpark AI Playwright 테스트")
    print("-" * 50)
    
    result = ask_genspark("안녕하세요, 테스트입니다")
    print("응답:", result[:500] if len(result) > 500 else result)
