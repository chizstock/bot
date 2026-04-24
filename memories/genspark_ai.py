"""
GenSpark AI Plus - API 기반 연동
주식 분석, 뉴스 요약, 데이터 해석 등에 활용

API Key 형식:
- gsk-eyJjb2dlbl9pZCI6... (Base64 encoded JSON)
- JSON 내용: cogen_id, key_id, ctime, claude_model 정보
"""
import json
import base64
import requests
import os
from datetime import datetime

# === API 설정 ===
API_KEY = "gsk-eyJjb2dlbl9pZCI6IjkyNWVkMTAxLWE0ZWYtNGI4Ni1iN2JjLTUzYTY5ZGExZjBmNCIsImtleV9pZCI6IjI0MmU1YmI0LTkzMDktNDBiMi05YmNjLTI4NWE4YmFhYWNmZiIsImN0aW1lIjoxNzc3MDEzNDYzLCJjbGF1ZGVfYmlnX21vZGVsIjpudWxsLCJjbGF1ZGVfbWlkZGxlX21vZGVsIjpudWxsLCJjbGF1ZGVfc21hbGxfbW9kZWwiOm51bGx9fLtCgMOZ_gUfoT322q-5t5GU_Y_0OyknMTraktRlR6eD"
BASE_URL = "https://www.genspark.ai/api"

# API 키 파싱
def parse_api_key(api_key):
    """API 키에서 정보 추출"""
    if api_key.startswith('gsk-'):
        token = api_key[4:]  # 'gsk-' 제거
        # 패딩 추가
        padding = 4 - len(token) % 4
        if padding != 4:
            token += '=' * padding
        try:
            decoded = base64.b64decode(token)
            # JSON 부분만 추출 (뒤의 바이너리 제거)
            json_str = decoded.decode('utf-8', errors='ignore').split('}')[0] + '}'
            return json.loads(json_str)
        except:
            pass
    return None


class GenSparkAPI:
    """GenSpark AI Plus API 클라이언트"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or API_KEY
        self.key_info = parse_api_key(self.api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://www.genspark.ai',
            'Referer': 'https://www.genspark.ai/',
        })
        
    def chat(self, message, model="claude-sonnet-4.5", stream=False):
        """
        AI 채팅 API 호출
        
        Args:
            message: 사용자 메시지
            model: 사용할 모델
            stream: 스트리밍 여부
            
        Returns:
            AI 응답
        """
        # 가능한 엔드포인트들 시도
        endpoints = [
            f"{BASE_URL}/chat",
            f"{BASE_URL}/superagent",
            f"{BASE_URL}/agents/chat",
            "https://www.genspark.ai/api/chat",
            "https://www.genspark.ai/api/superagent",
        ]
        
        payload = {
            "message": message,
            "model": model,
            "stream": stream,
        }
        
        if self.key_info:
            payload["cogen_id"] = self.key_info.get("cogen_id")
            payload["key_id"] = self.key_info.get("key_id")
        
        last_error = None
        for endpoint in endpoints:
            try:
                response = self.session.post(
                    endpoint,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # 응답에서 텍스트 추출
                        if isinstance(data, dict):
                            return data.get('response') or data.get('message') or data.get('text') or str(data)
                        return str(data)
                    except:
                        return response.text
                        
                elif response.status_code == 401:
                    last_error = "API 인증 실패: 키가 유효하지 않습니다."
                elif response.status_code == 404:
                    continue  # 다음 엔드포인트 시도
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                continue
                
        return f"API 호출 실패: {last_error}"
    
    def analyze_stock(self, stock_name, stock_code=None):
        """주식 분석"""
        code_str = f"({stock_code})" if stock_code else ""
        prompt = f"""{stock_name}{code_str} 종목을 분석해주세요.

다음 내용을 포함해주세요:
1. 기업 개요 및 사업 모델
2. 최근 실적 및 재무 상태  
3. 투자 포인트 및 리스크
4. 투자 의견 (단기/중기)

한국어로 작성해주세요."""
        
        return self.chat(prompt)
    
    def summarize(self, text, max_length=500):
        """텍스트 요약"""
        prompt = f"""다음 내용을 {max_length}자 이내로 요약해주세요:

{text}

요약 형식:
📌 핵심 요약
• 주요 포인트
💡 시장 영향"""
        
        return self.chat(prompt)


# === 편의 함수 ===

def ask_genspark(message, api_key=None):
    """GenSpark AI에 질문"""
    client = GenSparkAPI(api_key)
    return client.chat(message)

def analyze_stock_genspark(stock_name, stock_code=None, api_key=None):
    """주식 분석"""
    client = GenSparkAPI(api_key)
    return client.analyze_stock(stock_name, stock_code)

def summarize_genspark(text, max_length=500, api_key=None):
    """텍스트 요약"""
    client = GenSparkAPI(api_key)
    return client.summarize(text, max_length)


# === kis_utils.py 통합용 ===

def quick_chat(message):
    """kis_utils.py 통합용"""
    return ask_genspark(message)


def analyze_with_genspark(stock_name, stock_code=None):
    """kis_utils.py 통합용 - 주식 분석"""
    return analyze_stock_genspark(stock_name, stock_code)


def summarize_with_genspark(text, max_length=500):
    """kis_utils.py 통합용 - 요약"""
    return summarize_genspark(text, max_length)


if __name__ == "__main__":
    # 테스트
    print("GenSpark AI API 테스트")
    print("-" * 50)
    
    # API 키 정보 출력
    client = GenSparkAPI()
    print("API Key Info:", client.key_info)
    print()
    
    # 간단 테스트
    result = ask_genspark("안녕하세요, 테스트입니다")
    print("응답:", result[:500] if len(result) > 500 else result)
