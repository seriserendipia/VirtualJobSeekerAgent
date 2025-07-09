import os
from openai import OpenAI


def init_openai_client() -> OpenAI:
    """
    初始化 OpenAI 客户端：
    - 在 Colab 中使用 userdata
    - 本地用 .env
    - 检查 API key 是否可用
    - 返回可用的 OpenAI 客户端对象
    """
    try:
        from google.colab import userdata  # type: ignore
        os.environ['OPENAI_API_KEY'] = userdata.get('OPENAI_API_KEY')
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception as e:
        print(f"Could not load API key. Please ensure it's set up correctly. Error: {e}")

    print("🔑 API key found. Testing connection to OpenAI...")

    try:
        # 初始化客户端
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

        # 简单调用测试
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello, ChatGPT!'"}
            ]
        )
        response_message = chat_completion.choices[0].message.content
        print("\n✅ Success! The API key is working.")
        print(f"🤖 ChatGPT's response: {response_message}")

        return client

    except openai.AuthenticationError:
        print("\n❌ Authentication Error: The provided OpenAI API key is invalid or has expired.")
    except openai.RateLimitError:
        print("\n❌ Rate Limit Error: You have exceeded your current quota.")
    except openai.APIConnectionError as e:
        print("\n❌ Connection Error: Failed to connect to OpenAI's API.")
        print(f"   Please check your network connection. Details: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

    raise RuntimeError("Failed to initialize OpenAI client. Please check your API key and network.")


if __name__ == "__main__":
    # 测试一下封装好的函数
    client = init_openai_client()
