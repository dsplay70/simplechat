# lambda/index.py
import json
import os
import requests 
import re  # 正規表現モジュールをインポート

# 公開APIのURL
FASTAPI_ENDPOINT_URL = "https://e547-35-240-156-219.ngrok-free.app/"

def lambda_handler(event, context):
     try:
         print("Received event:", json.dumps(event))

         # Cognitoで認証されたユーザー情報を取得
         user_info = None
         if 'requestContext' in event and 'authorizer' in event['requestContext']:
             user_info = event['requestContext']['authorizer']['claims']
             print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

         # リクエストボディの解析
         body = json.loads(event['body'])
         message = body['message']
         conversation_history = body.get('conversationHistory', [])

         print("Processing message:", message)

         # FastAPIに送信するペイロードの作成
         fastapi_payload = {
                  "message": message,
                  "conversationHistory": conversation_history
                  # 必要に応じてユーザー情報などを追加
         }
         print("Sending payload to FastAPI:", json.dumps(fastapi_payload))

         # FastAPIのエンドポイントへPOSTリクエストを送信
         headers = {'Content-Type': 'application/json'}
         response = requests.post(FASTAPI_ENDPOINT_URL, headers=headers, json=fastapi_payload)
         response.raise_for_status()  # エラーレスポンスの場合に例外を発生させる

         fastapi_response = response.json()
         print("FastAPI response:", json.dumps(fastapi_response))

         # FastAPIからの応答を解析
         if not fastapi_response.get('response'):
             raise Exception("No 'response' in FastAPI response")
         assistant_response = fastapi_response['response']
         updated_conversation_history = fastapi_response.get('conversationHistory', conversation_history + [{"role": "user", "content": message}, {"role": "assistant", "content": assistant_response}])

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
                 "conversationHistory": updated_conversation_history
             })
        }

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request Error: {e}")
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
                    "error": f"Failed to connect to FastAPI: {e}"
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
