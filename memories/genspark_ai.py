"""
GenSpark AI Plus - AI 채팅 인터페이스 연동 모듈
주식 분석, 뉴스 요약, 데이터 해석 등에 활용

사용법:
    from genspark_ai import GenSparkChat
    
    # AI 채팅 시작
    with GenSparkChat() as chat:
        response = chat.send("삼성전자 분석해줘")
        print(response)
        
    # 또는 편의 함수 사용
    from genspark_ai import ask_genspark
    result = ask_genspark("오늘 시장 어때?")
"""
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


class GenSparkChat:
    """
    GenSpark AI Plus AI 채팅 인터페이스
    
    https://www.genspark.ai 의 AI Chat 페이지를 자동화합니다.
    """
    
    def __init__(self, headless=True, timeout=60):
        """
        Args:
            headless: True면 브라우저 창을 띄우지 않음
            timeout: 요소 대기 시간(초)
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.wait = None
        self.chat_url = "https://www.genspark.ai"
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
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        self.wait = WebDriverWait(self.driver, self.timeout)
        
    def start_chat(self):
        """
        AI 채팅 세션 시작
        
        Returns:
            self (체이닝 가능)
        """
        if not self.driver:
            self._init_driver()
            
        # AI Chat 페이지로 이동
        self.driver.get(self.chat_url)
        time.sleep(5)  # 페이지 로딩 대기
        
        # AI Chat 버튼/입력창 찾기
        self._find_chat_input()
        
        self.session_active = True
        return self
        
    def _find_chat_input(self):
        """채팅 입력창 찾기 (여러 가능성 시도)"""
        input_selectors = [
            # 일반적인 채팅 입력창
            "textarea[placeholder*='message']",
            "textarea[placeholder*='질문']",
            "textarea[placeholder*='입력']",
            "div[contenteditable='true']",
            "input[type='text']",
            # 특정 클래스/ID 패턴
            "[data-testid='chat-input']",
            "[data-testid='message-input']",
            ".chat-input",
            ".message-input",
            # GenSpark 특화
            "textarea",
            "[role='textbox']",
        ]
        
        for selector in input_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # 가장 아래쪽(최근) 입력창 선택
                    self.chat_input = elements[-1]
                    print(f"입력창 발견: {selector}")
                    return True
            except:
                continue
                
        # JavaScript로 찾기 시도
        try:
            self.chat_input = self.driver.execute_script("""
                // placeholder에 'message', '질문', '입력' 등이 포함된 요소
                const inputs = document.querySelectorAll('textarea, input, [contenteditable]');
                for (let el of inputs) {
                    const placeholder = el.getAttribute('placeholder') || '';
                    if (placeholder.toLowerCase().includes('message') || 
                        placeholder.includes('질문') || 
                        placeholder.includes('입력') ||
                        el.tagName === 'TEXTAREA') {
                        return el;
                    }
                }
                // 마지막 textarea 반환
                return document.querySelector('textarea');
            """)
            if self.chat_input:
                print("JavaScript로 입력창 발견")
                return True
        except:
            pass
            
        raise Exception("채팅 입력창을 찾을 수 없습니다.")
        
    def send(self, message, wait_for_response=True, response_timeout=60):
        """
        AI 채팅에 메시지 전송
        
        Args:
            message: 별낼 메시지
            wait_for_response: 응답 대기 여부
            response_timeout: 응답 최대 대기 시간(초)
            
        Returns:
            AI 응답 텍스트 (wait_for_response=True인 경우)
            또는 None (wait_for_response=False인 경우)
        """
        if not self.session_active:
            self.start_chat()
            
        # 입력창이 보이도록 스크롤
        self.driver.execute_script("arguments[0].scrollIntoView(true);", self.chat_input)
        time.sleep(1)
        
        # 메시지 입력
        self.chat_input.clear()
        self.chat_input.send_keys(message)
        time.sleep(0.5)
        
        # 전송 (Enter 키)
        self.chat_input.send_keys(Keys.RETURN)
        
        if not wait_for_response:
            return None
            
        # 응답 대기
        return self._wait_for_response(response_timeout)
        
    def _wait_for_response(self, timeout=60):
        """
        AI 응답 대기
        
        Args:
            timeout: 최대 대기 시간(초)
            
        Returns:
            응답 텍스트
        """
        start_time = time.time()
        last_response = ""
        stable_count = 0
        
        # 응답 선택자들
        response_selectors = [
            ".message-content",
            ".chat-message",
            ".response",
            ".answer",
            "[data-testid='message-content']",
            "[data-testid='assistant-message']",
            ".prose",
            ".markdown-body",
            "div[class*='message'] div[class*='content']",
            "div[class*='response']",
        ]
        
        while time.time() - start_time < timeout:
            try:
                # 모든 가능한 응답 요소 수집
                all_responses = []
                for selector in response_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        all_responses.extend([el.text for el in elements if el.text])
                    except:
                        continue
                        
                # JavaScript로도 찾기
                try:
                    js_responses = self.driver.execute_script("""
                        const messages = [];
                        // assistant/bot 메시지 찾기
                        document.querySelectorAll('div, article, section').forEach(el => {
                            const text = el.textContent || '';
                            if (text.length > 50 && 
                                (el.className.includes('message') || 
                                 el.className.includes('response') ||
                                 el.className.includes('answer') ||
                                 el.getAttribute('role') === 'assistant')) {
                                messages.push(text);
                            }
                        });
                        return messages;
                    """)
                    all_responses.extend(js_responses)
                except:
                    pass
                    
                # 중복 제거 및 필터링
                unique_responses = list(dict.fromkeys([r.strip() for r in all_responses if len(r.strip()) > 20]))
                
                if unique_responses:
                    # 가장 긴 응답 (보통 최신/완전한 응답)
                    current_response = max(unique_responses, key=len)
                    
                    if current_response != last_response:
                        last_response = current_response
                        stable_count = 0
                    else:
                        stable_count += 1
                        
                    # 응답이 안정화되면 반환
                    if stable_count >= 3 and len(current_response) > 100:
                        return current_response
                        
            except Exception as e:
                pass
                
            time.sleep(1)
            
        return last_response if last_response else "응답을 받지 못했습니다."
        
    def get_chat_history(self):
        """현재 채팅 히스토리 가져오기"""
        try:
            messages = self.driver.execute_script("""
                const history = [];
                document.querySelectorAll('[class*="message"], [class*="chat"]').forEach(el => {
                    const role = el.className.includes('user') ? 'user' : 'assistant';
                    const content = el.textContent;
                    if (content) history.push({role, content});
                });
                return history;
            """)
            return messages
        except:
            return []
            
    def clear_chat(self):
        """채팅 초기화 (새 세션 시작)"""
        try:
            # 새 채팅 버튼 찾기
            new_chat_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='new-chat'], button:contains('New'), .new-chat")
            new_chat_btn.click()
            time.sleep(2)
            self._find_chat_input()
        except:
            # 페이지 새로고침으로 대체
            self.driver.refresh()
            time.sleep(3)
            self._find_chat_input()
            
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


# === 전문 분석 프롬프트 ===

STOCK_ANALYSIS_PROMPT = """당신은 전문 주식 애널리스트입니다. {stock_name}({stock_code}) 종목에 대해 심층 분석해주세요.

다음 내용을 포함해주세요:

## 1. 기업 개요
- 주요 사업 영역
- 핵심 제품/서비스
- 시장 지위

## 2. 재무 분석
- 최근 분기 실적 추이
- 수익성 지표 (영업이익률, 순이익률)
- 재무건전성 (부채비율, 유동성)

## 3. 투자 포인트
- 성장 동력
- 경쟁 우위
- 모멘텀 요인

## 4. 리스크 요인
- 사업 리스크
- 시장 리스크
- 재무 리스크

## 5. 투자 의견
- 단기 전망 (1~3개월)
- 중기 전망 (6~12개월)
- 목표가 및 손절가 제시

한국어로 작성해주세요."""

NEWS_SUMMARY_PROMPT = """다음 뉴스/텍스트를 {max_length}자 이내로 요약해주세요:

{text}

요약 형식:
📌 핵심 요약 (2~3줄)
• 주요 포인트 (3~5개 불릿)
💡 시장 영향 및 전망

한국어로 작성해주세요."""

DATA_INTERPRET_PROMPT = """다음 데이터를 분석하고 투자적 관점에서 해석해주세요:

[데이터]
{data}

[컨텍스트]
{context}

분석 형식:
## 1. 데이터 개요
## 2. 핵심 패턴/인사이트
## 3. 투자적 의미
## 4. 주의사항 및 리스크

한국어로 작성해주세요."""


# === 편의 함수 ===

def ask_genspark(message, mode="pro", headless=True):
    """
    GenSpark AI Chat에 간단하게 질문
    
    Args:
        message: 질문 내용
        mode: "pro" 또는 "standard"
        headless: True면 백그라운드 실행
        
    Returns:
        AI 응답 텍스트
    """
    with GenSparkChat(headless=headless) as chat:
        return chat.send(message)

def analyze_stock_genspark(stock_name, stock_code=None):
    """
    GenSpark AI로 주식 종목 분석
    
    Args:
        stock_name: 종목명
        stock_code: 종목코드 (선택)
        
    Returns:
        분석 결과
    """
    code_str = f"({stock_code})" if stock_code else ""
    prompt = STOCK_ANALYSIS_PROMPT.format(
        stock_name=stock_name,
        stock_code=code_str
    )
    
    with GenSparkChat() as chat:
        return chat.send(prompt)

def summarize_genspark(text, max_length=500):
    """
    GenSpark AI로 텍스트 요약
    
    Args:
        text: 요약할 텍스트
        max_length: 최대 길이
        
    Returns:
        요약 결과
    """
    prompt = NEWS_SUMMARY_PROMPT.format(
        text=text,
        max_length=max_length
    )
    
    with GenSparkChat() as chat:
        return chat.send(prompt)

def interpret_data_genspark(data, context=""):
    """
    GenSpark AI로 데이터 해석
    
    Args:
        data: 데이터 내용
        context: 추가 컨텍스트
        
    Returns:
        해석 결과
    """
    prompt = DATA_INTERPRET_PROMPT.format(
        data=data,
        context=context
    )
    
    with GenSparkChat() as chat:
        return chat.send(prompt)


# === kis_utils.py 통합용 함수 ===

def quick_chat(message):
    """kis_utils.py 통합용: 간단 채팅"""
    return ask_genspark(message)


if __name__ == "__main__":
    # 테스트
    print("GenSpark AI Chat 모듈 테스트")
    print("-" * 50)
    
    # 간단 질문 테스트
    # result = ask_genspark("안녕하세요, 삼성전자에 대해 알려주세요")
    # print(result)
    
    # 주식 분석 테스트
    # result = analyze_stock_genspark("삼성전자", "005930")
    # print(result)
