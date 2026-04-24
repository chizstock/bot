"""
GenSpark AI Plus - 디버깅용 테스트 스크립트
headless=False로 실행하여 페이지 구조 확인
"""
import sys
sys.path.insert(0, 'memories')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os

COOKIE_FILE = os.path.join(os.path.dirname(__file__), "genspark_cookies.json")

def debug_genspark():
    """GenSpark 페이지 구조 디버깅"""
    
    # headless=False로 설정 (화면에 보임)
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        # 쿠키 로드
        driver.get("https://www.genspark.ai")
        time.sleep(2)
        
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                try:
                    cookie['domain'] = '.genspark.ai'
                    driver.add_cookie(cookie)
                except:
                    pass
        
        # AI 채팅 페이지로 이동
        driver.get("https://www.genspark.ai/agents?type=ai_chat")
        print("페이지 로드 완료. 10초 후 페이지 구조 분석...")
        time.sleep(10)
        
        # 페이지 구조 분석
        print("\n=== 페이지 구조 분석 ===")
        
        # 모든 input/textarea 요소 찾기
        inputs = driver.find_elements(By.TAG_NAME, "textarea")
        print(f"\ntextarea 요소 수: {len(inputs)}")
        for i, inp in enumerate(inputs[:5]):
            print(f"  [{i}] placeholder: {inp.get_attribute('placeholder')}, visible: {inp.is_displayed()}")
            
        inputs2 = driver.find_elements(By.TAG_NAME, "input")
        print(f"\ninput 요소 수: {len(inputs2)}")
        for i, inp in enumerate(inputs2[:10]):
            placeholder = inp.get_attribute('placeholder') or ''
            type_attr = inp.get_attribute('type') or ''
            if 'text' in type_attr or placeholder:
                print(f"  [{i}] type: {type_attr}, placeholder: {placeholder}, visible: {inp.is_displayed()}")
        
        # contenteditable 요소
        editables = driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
        print(f"\ncontenteditable 요소 수: {len(editables)}")
        for i, el in enumerate(editables[:5]):
            print(f"  [{i}] text: {el.text[:50] if el.text else 'empty'}, visible: {el.is_displayed()}")
            
        # placeholder로 찾기
        all_inputs = driver.find_elements(By.CSS_SELECTOR, "textarea, input, div[contenteditable]")
        print(f"\n전체 입력 요소 수: {len(all_inputs)}")
        for i, el in enumerate(all_inputs):
            placeholder = el.get_attribute('placeholder') or ''
            if '무엇' in placeholder or '도와' in placeholder or 'message' in placeholder.lower():
                print(f"  >>> FOUND [{i}] tag: {el.tag_name}, placeholder: {placeholder}")
                print(f"       location: {el.location}, size: {el.size}")
                print(f"       displayed: {el.is_displayed()}, enabled: {el.is_enabled()}")
        
        print("\n=== 브라우저를 직접 확인하세요 ===")
        print("10분간 대기합니다...")
        time.sleep(600)  # 10분 대기 (직접 확인 시간)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_genspark()
