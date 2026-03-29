# 依赖镜像 —— 只安装 Python 依赖，不打包源码
# 源码在 docker-compose 启动时通过 volume 挂载进来
FROM crpi-pqzengdgydwtnauc.cn-shanghai.personal.cr.aliyuncs.com/mjxj-env/python:3.11

WORKDIR /app

# gcc / libffi-dev 用于编译 cryptography 等 C 扩展
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# 创建最小占位包，让 setuptools 能解析并安装所有 [project.dependencies]
# 安装完成后删除占位代码；运行时真正的 backend/ 由 volume 挂载覆盖
RUN mkdir -p backend && touch backend/__init__.py \
    && pip install --no-cache-dir --upgrade pip setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir . -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && rm -rf backend

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
