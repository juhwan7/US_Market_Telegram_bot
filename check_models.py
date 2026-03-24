import google.generativeai as genai

GEMINI_KEY = "..." 

genai.configure(api_key=GEMINI_KEY)

def list_available_models():
    print("🔍 사용 가능한 Gemini 모델 목록을 조회합니다...\n")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ 모델명: {m.name}")
                print(f"   - 설명: {m.description}")
                print(f"   - 입력 제한(TPM): {m.input_token_limit}")
                print("-" * 50)
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    list_available_models()