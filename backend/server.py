import os
import json
import logging
import traceback
import sys
import re
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🔄 开始导入模块...")
try:
    from generate_followup_email import generate_email, modify_email
    from web_search_agent import find_recruiter_email_via_web_search, setup_aurite_for_recruiter_search
    print("✅ generate_followup_email 导入成功")
    
    from email_handling import send_email_via_google_api
    print("✅ email_handling 导入成功")
    
    from aurite_service import get_aurite
    print("✅ aurite_service 导入成功")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    traceback.print_exc()

# 环境配置函数
def get_environment_config():
    """
    根据环境变量检测和返回当前环境配置
    """
    # 检查环境变量
    environment = os.environ.get('ENVIRONMENT')
    
    # 如果没有设置ENVIRONMENT，进行自动检测
    if not environment:
        # 检测Railway环境
        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'):
            environment = 'production'
        # 检测是否有非默认端口（云端特征）
        elif os.environ.get('PORT') and os.environ.get('PORT') != '5000':
            environment = 'production'
        else:
            environment = 'local'
    
    # 基础配置
    config = {
        'environment': environment,
        'debug': environment == 'local',
        'host': '0.0.0.0',
        'port': int(os.environ.get('PORT', 5000))
    }
    
    # CORS配置
    if environment == 'production':
        config['cors_origins'] = [
            "chrome-extension://*",
            "moz-extension://*", 
            "https://railway.app",
            "https://*.railway.app"
        ]
    else:
        config['cors_origins'] = [
            "chrome-extension://*",
            "moz-extension://*",
            "http://localhost:*",
            "http://127.0.0.1:*"
        ]
    
    return config

# 获取配置
config = get_environment_config()

# 创建 FastAPI 应用
app = FastAPI(
    title="VirtualJobSeekerAgent API",
    description="虚拟求职代理 API 服务",
    version="2.0.0",
    debug=config['debug']
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config['cors_origins'],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 请求响应模型
class GenerateEmailRequest(BaseModel):
    job_description: str = Field(..., description="职位描述")
    resume: str = Field(..., description="简历内容")
    user_prompt: Optional[str] = Field(None, description="用户自定义提示")
    current_subject: Optional[str] = Field(None, description="当前邮件主题")
    current_body: Optional[str] = Field(None, description="当前邮件内容")

class ModifyEmailRequest(BaseModel):
    resume: str = Field(..., description="简历内容")
    job_description: str = Field(..., description="职位描述")
    current_subject: str = Field(..., description="当前邮件主题")
    current_body: str = Field(..., description="当前邮件内容")
    user_feedback: str = Field(..., description="用户反馈/修改要求")

class GenerateAndModifyEmailRequest(BaseModel):
    job_description: Optional[str] = Field(None, description="职位描述")
    resume: Optional[str] = Field(None, description="简历内容")
    user_prompt: Optional[str] = Field(None, description="用户自定义提示")
    # 修改邮件相关字段
    current_subject: Optional[str] = Field(None, description="当前邮件主题")
    current_body: Optional[str] = Field(None, description="当前邮件内容")
    user_feedback: Optional[str] = Field(None, description="用户反馈/修改要求")

class SendEmailRequest(BaseModel):
    access_token: str = Field(..., description="Google API access token")
    subject: str = Field(..., description="邮件主题")
    body: str = Field(..., description="邮件内容")
    to: str = Field(..., description="收件人邮箱")

class FindRecruiterEmailRequest(BaseModel):
    job_description: Optional[str] = Field(None, description="职位描述")
    company_name: Optional[str] = Field(None, description="公司名称")
    job_title: Optional[str] = Field(None, description="职位标题")

# 中间件：请求日志记录
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求和响应的详细信息"""
    print("=" * 60)
    print(f"🌐 [INCOMING REQUEST] {request.method} {request.url.path}")
    print(f"📍 Client: {request.client.host if request.client else 'Unknown'}")
    print(f"🌍 Host: {request.url.hostname}")
    print(f"🔗 URL: {str(request.url)}")
    print(f"📋 Headers:")
    for name, value in request.headers.items():
        print(f"   {name}: {value}")
    
    # 检查是否是 OPTIONS 请求
    if request.method == 'OPTIONS':
        print("🔄 这是一个 CORS 预检请求")
    
    print("=" * 60)
    sys.stdout.flush()
    
    # 处理请求
    response = await call_next(request)
    
    # 记录响应
    print("=" * 60)
    print(f"📤 [RESPONSE] Status: {response.status_code}")
    print(f"📋 Response Headers:")
    for name, value in response.headers.items():
        print(f"   {name}: {value}")
    print("=" * 60)
    sys.stdout.flush()
    
    return response

# 工具函数：验证扩展请求
def validate_extension_request(request: Request):
    """验证请求是否来自扩展"""
    if request.headers.get('X-From-Extension') != 'true':
        logger.warning("Request missing 'X-From-Extension: true' header.")
        raise HTTPException(status_code=403, detail="Forbidden")

# 依赖注入：扩展验证
async def require_extension_header(request: Request):
    validate_extension_request(request)
    return True

# API 端点定义

@app.get("/")
async def root(request: Request):
    """根路径端点，验证服务状态 - 移除扩展验证以支持Railway健康检查"""
    print("🏠 [ROOT] 收到根路径请求")
    print(f"🏠 Request headers: {dict(request.headers)}")
    print(f"🏠 Request origin: {request.headers.get('Origin', 'No Origin')}")
    
    # 检查是否来自扩展
    is_from_extension = request.headers.get('X-From-Extension') == 'true'
    
    logger.info(f'Received GET request to root from {request.client.host if request.client else "Unknown"}')
    
    return {
        "message": "Aloha from Python backend!",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": config['environment'],
        "from_extension": is_from_extension
    }

@app.post("/generate_email")
async def generate_email_endpoint(
    request: GenerateEmailRequest,
    http_request: Request,
    _: bool = Depends(require_extension_header)
):
    """生成邮件端点"""
    print("📧 [GENERATE EMAIL] 开始处理生成邮件请求")
    logger.info(f'Received generate_email request from {http_request.client.host if http_request.client else "Unknown"}')
    
    # 添加详细日志
    print(f"📧 [DEBUG] 请求数据:")
    print(f"📧 [DEBUG] - job_description length: {len(request.job_description) if request.job_description else 0}")
    print(f"📧 [DEBUG] - resume length: {len(request.resume) if request.resume else 0}")
    print(f"📧 [DEBUG] - user_prompt: {request.user_prompt}")
    
    try:
        print("📧 [DEBUG] 开始调用 generate_email 函数...")
        
        # 调用邮件生成函数，注意参数名映射
        generation_result = await generate_email(
            resume_content=request.resume,
            jd_content=request.job_description
        )
        
        print(f"📧 [DEBUG] generate_email 返回结果类型: {type(generation_result)}")
        print(f"📧 [DEBUG] generate_email 返回结果: {generation_result}")
        
        # 处理返回结果的不同格式
        if isinstance(generation_result, dict):
            # 检查新的返回格式
            if (generation_result.get("status") == "success" and 
                "data" in generation_result and 
                "email" in generation_result["data"]):
                email_data = generation_result["data"]["email"]
                print(f"📧 [DEBUG] 找到新格式数据: {email_data}")
                if "subject" in email_data and "body" in email_data:
                    final_response = {
                        "status": "Success",
                        "email": email_data,
                        "timestamp": datetime.now().isoformat()
                    }
                    print(f"📧 [DEBUG] 最终响应: {final_response}")
                    return final_response
            # 检查直接格式
            elif "subject" in generation_result and "body" in generation_result:
                print(f"📧 [DEBUG] 找到直接格式数据: {generation_result}")
                final_response = {
                    "status": "Success",
                    "email": generation_result,
                    "timestamp": datetime.now().isoformat()
                }
                print(f"📧 [DEBUG] 最终响应: {final_response}")
                return final_response
        
        print(f"📧 [ERROR] 意外的返回格式: {generation_result}")
        logger.error(f"Unexpected output from generate_email: {generation_result}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during email generation.")
            
    except Exception as e:
        print(f"📧 [ERROR] 处理邮件生成请求时出错: {e}")
        logger.error(f'Failed to process email generation request: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_and_modify_email")
async def generate_and_modify_email_endpoint(
    request: GenerateAndModifyEmailRequest,
    http_request: Request,
    _: bool = Depends(require_extension_header)
):
    """生成和修改邮件端点"""
    print("📧 [GENERATE AND MODIFY EMAIL] 开始处理请求")
    logger.info(f'Received generate_and_modify_email request from {http_request.client.host if http_request.client else "Unknown"}')
    
    try:
        # 如果提供了修改邮件的必要字段，执行修改
        if (request.current_subject and request.current_body and request.user_feedback 
            and request.resume and request.job_description):
            modification_result = await modify_email(
                resume_content=request.resume,
                jd_content=request.job_description,
                current_email_subject=request.current_subject,
                current_email_body=request.current_body,
                user_feedback=request.user_feedback
            )
            
            # 处理修改邮件的返回结果
            email_data = None
            if isinstance(modification_result, dict):
                if (modification_result.get("status") == "success" and 
                    "data" in modification_result and 
                    "email" in modification_result["data"]):
                    email_data = modification_result["data"]["email"]
                elif "subject" in modification_result and "body" in modification_result:
                    email_data = modification_result
            
            if email_data and "subject" in email_data and "body" in email_data:
                return {
                    "status": "Success",
                    "email": email_data,
                    "action": "modification",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Unexpected output from modify_email: {modification_result}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred during email modification.")
        
        # 如果提供了生成邮件的必要字段，执行生成
        elif request.job_description and request.resume:
            generation_result = await generate_email(
                resume_content=request.resume,
                jd_content=request.job_description
            )
            
            # 处理生成邮件的返回结果
            email_data = None
            if isinstance(generation_result, dict):
                if (generation_result.get("status") == "success" and 
                    "data" in generation_result and 
                    "email" in generation_result["data"]):
                    email_data = generation_result["data"]["email"]
                elif "subject" in generation_result and "body" in generation_result:
                    email_data = generation_result
            
            if email_data and "subject" in email_data and "body" in email_data:
                return {
                    "status": "Success",
                    "email": email_data,
                    "action": "generation",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Unexpected output from generate_email: {generation_result}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred during email generation.")
        
        else:
            raise HTTPException(status_code=400, detail="Missing required fields for email generation or modification.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to process email generation/modification request: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/find_recruiter_email")
async def find_recruiter_email_endpoint(
    request: FindRecruiterEmailRequest,
    http_request: Request,
    _: bool = Depends(require_extension_header)
):
    """查找招聘人员邮箱端点"""
    print("🔍 [FIND RECRUITER EMAIL] 开始处理查找邮箱请求")
    logger.info('Received find_recruiter_email request')
    
    try:
        # 检查是否提供了必要的搜索信息
        if not request.company_name:
            raise HTTPException(
                status_code=400, 
                detail="Missing required field: company_name"
            )
        
        # 调用搜索函数
        print(f"🔍 [DEBUG] 开始搜索 company_name: {request.company_name}, job_title: {request.job_title}")
        
        search_result = await find_recruiter_email_via_web_search(
            company_name=request.company_name,
            job_title=request.job_title or ""
        )
        
        print(f"🔍 [DEBUG] 搜索结果: {search_result}")
        
        # 确保返回正确的格式
        response = {
            "status": "Success",
            "result": search_result,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"🔍 [DEBUG] 最终响应: {response}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to process recruiter email search: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-email")
async def send_email_endpoint(
    request: SendEmailRequest,
    http_request: Request,
    _: bool = Depends(require_extension_header)
):
    """发送邮件端点"""
    print("📤 [SEND EMAIL] 开始处理发送邮件请求")
    logger.info("[send_email] Starting email request processing")
    
    try:
        # 构建邮件数据
        email_data = {
            'subject': request.subject,
            'body': request.body,
            'to': request.to,
            'access_token': request.access_token
        }
        
        # 发送邮件
        success, response = await send_email_via_google_api(email_data)
        
        if success:
            return {
                "success": True,
                "message": "Email sent successfully!",
                "google_response": response,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Failed to send email",
                "error": response,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error processing email send request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "message": "Internal Server Error", "error": str(e)})

@app.post("/send-email-from-file")
async def send_email_from_file_endpoint(
    http_request: Request,
    _: bool = Depends(require_extension_header)
):
    """从文件发送邮件端点"""
    print("📂 [SEND EMAIL FROM FILE] 开始处理从文件发送邮件请求")
    logger.info("[send_email_from_file] Starting request processing")
    
    try:
        # 解析请求数据
        request_data = await http_request.json()
        
        # 验证必要字段
        required_fields = ['emailFileName', 'access_token']
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail={"success": False, "message": f"Missing required fields: {missing_fields}"}
            )
        
        email_file_name = request_data['emailFileName']
        access_token = request_data['access_token']
        
        # 读取邮件文件
        file_path = os.path.join(os.getcwd(), email_file_name)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404, 
                detail={"success": False, "message": f"Email file '{email_file_name}' not found."}
            )
        
        with open(file_path, 'r', encoding='utf-8') as file:
            email_content = json.load(file)
        
        # 验证邮件内容格式
        email_required_fields = ['subject', 'body', 'to']
        missing_email_fields = [field for field in email_required_fields if field not in email_content]
        if missing_email_fields:
            raise HTTPException(
                status_code=400, 
                detail={"success": False, "message": f"Email file missing required fields: {missing_email_fields}"}
            )
        
        # 添加access_token
        email_content['access_token'] = access_token
        
        # 发送邮件
        success, response = await send_email_via_google_api(email_content)
        
        if success:
            return {
                "success": True,
                "message": "Email sent successfully from file!",
                "google_response": response,
                "email_file": email_file_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Failed to send email from file",
                "error": response,
                "email_file": email_file_name,
                "timestamp": datetime.now().isoformat()
            }
            
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, 
            detail={"success": False, "message": f"Error: Invalid JSON format in '{request_data.get('emailFileName', 'unknown')}'."}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request to send email from file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "message": "Internal Server Error", "error": str(e)})

# FastAPI 应用启动配置
if __name__ == '__main__':
    import uvicorn
    print("🔧 开始启动服务器...")
    print(f"Python 版本: {sys.version}")
    print(f"FastAPI 应用: {app.title}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"环境: {config['environment']}")
    print(f"端口: {config['port']}")
    print(f"CORS Origins: {config['cors_origins']}")
    
    uvicorn.run(
        app,
        host=config['host'],
        port=config['port'],
        log_level="info" if config['debug'] else "warning"
    )
