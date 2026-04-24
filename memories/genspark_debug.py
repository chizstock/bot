"""
GenSpark AI Plus - 간단 디버깅
입력창 정볼만 빠르게 확인
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
    print("페이지 로드 중... 15초 대기")
    time.sleep(15)
    
    # 페이지 구조 분석
    print("\n=== 입력창 검색 결과 ===")
    
    # JavaScript로 모든 입력 요소 검색
    result = driver.execute_script("""
        const results = [];
        
        // 1. textarea 검색
        document.querySelectorAll('textarea').forEach((el, i) => {
            results.push({
                type: 'textarea',
                index: i,
                placeholder: el.getAttribute('placeholder') || '',
                visible: el.offsetParent !== null,
                rect: el.getBoundingClientRect()
            });
        });
        
        // 2. input 검색
        document.querySelectorAll('input').forEach((el, i) => {
            const type = el.getAttribute('type') || 'text';
            const placeholder = el.getAttribute('placeholder') || '';
            if (type === 'text' || type === 'search' || placeholder) {
                results.push({
                    type: 'input:' + type,
                    index: i,
                    placeholder: placeholder,
                    visible: el.offsetParent !== null,
                    rect: el.getBoundingClientRect()
                });
            }
        });
        
        // 3. contenteditable 검색
        document.querySelectorAll('[contenteditable="true"]').forEach((el, i) => {
            results.push({
                type: 'contenteditable',
                index: i,
                text: el.innerText.substring(0, 50),
                visible: el.offsetParent !== null,
                rect: el.getBoundingClientRect()
            });
        });
        
        // 4. 특정 placeholder 검색
        const allInputs = document.querySelectorAll('textarea, input, div[contenteditable]');
        const targets = [];
        allInputs.forEach((el, i) => {
            const placeholder = el.getAttribute('placeholder') || '';
            if (placeholder.includes('무엇') || placeholder.includes('도와') || placeholder.includes('message')) {
                targets.push({
                    tag: el.tagName,
                    placeholder: placeholder,
                    visible: el.offsetParent !== null,
                    rect: el.getBoundingClientRect()
                });
            }
        });
        
        return {all: results, targets: targets, pageText: document.body.innerText.substring(0, 500)};
    """)
    
    print(f"\n전체 입력 요소 수: {len(result['all'])}")
    for item in result['all'][:10]:
        print(f"  - {item['type']}: placeholder='{item['placeholder']}', visible={item['visible']}")
    
    print(f"\n타겟 입력창 (placeholder에 '무엇/도와/message' 포함): {len(result['targets'])}")
    for item in result['targets']:
        print(f"  >>> {item['tag']}: '{item['placeholder']}', visible={item['visible']}")
        print(f"      위치: x={item['rect']['x']:.0f}, y={item['rect']['y']:.0f}, w={item['rect']['width']:.0f}, h={item['rect']['height']:.0f}")
    
    print("\n=== 페이지 텍스트 미리보기 ===")
    print(result['pageText'])
    
    print("\n=== 완료 ===")
    print("브라우저는 30초 후 자동으로 닫힙니다...")
    time.sleep(30)
    
finally:
    driver.quit()
    print("브라우저 종료")
