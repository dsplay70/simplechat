# lambda/index.py
import json
import os
import urllib.request
import urllib.parse
import ssl  # HTTPSリクエストに必要

# 公開APIのURL
FASTAPI_ENDPOINT_URL = "https://e547-35-240-156-219.ngrok-free.app/"

# APIの設定値
MAX_NEW_TOKENS = 512
DO_SAMPLE = True
TEMPERATURE = 0.7
TOP_P = 0.9

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # Cognitoで認証されたユーザー情報を取得（必要に応じてFastAPIに転送できます）
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

            # リクエストボディの解析
            body = json.loads(event['body'])
            message = body['message']

            print("Processing message:", message)

            # FastAPIに送信するペイロードの作成
            fastapi_payload = {
                    "prompt": message,
                    "max_new_tokens": MAX_NEW_TOKENS,
                    "do_sample": DO_SAMPLE,
                    "temperature": TEMPERATURE,
                    "top_p": TOP_P
                    }
            payload_json = json.dumps(fastapi_payload).encode('utf-8')
            print("Sending payload to FastAPI:", payload_json.decode('utf-8'))

            # HTTPSコンテキストの作成（SSL証明書の検証をスキップしない場合）
            context = ssl.create_default_context()
            # SSL証明書の検証をスキップする場合（推奨されません）
            # context = ssl._create_unverified_context()

            # FastAPIのエンドポイントへのリクエストを作成
            req = urllib.request.Request(FASTAPI_ENDPOINT_URL, data=payload_json, headers={'Content-Type': 'application/json'}, method='POST')

            # FastAPIのエンドポイントへPOSTリクエストを送信
            with urllib.request.urlopen(req, context=context) as res:
                response_body = res.read().decode('utf-8')
                fastapi_response = json.loads(response_body)
                print("FastAPI response:", json.dumps(fastapi_response))

                # FastAPIからの応答を解析
                if not fastapi_response.get('generated_text'):
                    raise Exception("No 'generated_text' in FastAPI response")
                assistant_response = fastapi_response['generated_text']

                # 成功レスポンスの返却
                return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                            "Access-Control-Allow-Methods": "OPTIONS,POST"
                            },
                        "body": json.dumps({
                            "success": True,
                            "response": assistant_response,
                            })
                        }

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        return {
                "statusCode": e.code,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                    },
                "body": json.dumps({
                    "success": False,
                    "error": f"Failed to connect to FastAPI: HTTP Error {e.code} - {e.reason}"
                    })
                }
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                    },
                "body": json.dumps({
                    "success": False,
                    "error": f"Failed to connect to FastAPI: URL Error - {e.reason}"
                    })
                }
    except Exception as error:
        print("Error:", str(error))
        return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                    },
                "body": json.dumps({
                    "success": False,
                    "error": str(error)
                    })
                }
