# 使用 Python 3.11 作为基础镜像（aurite 包兼容性更好）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制环境变量文件（如果存在）
COPY .env* ./

# 创建缓存目录
RUN mkdir -p .aurite_cache

# 暴露端口
EXPOSE 5000

# 设置启动命令
CMD ["python", "backend/server.py"]