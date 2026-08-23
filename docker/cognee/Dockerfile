FROM cognee/cognee:main

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY sitecustomize.py /opt/mindcart/sitecustomize.py
COPY sitecustomize.py /app/.venv/lib/python3.12/site-packages/sitecustomize.py
ENV PYTHONPATH=/opt/mindcart

USER root
# Keep the image's Cognee version; only add the Falkor adapter and a redis
# new enough for falkordb (redis.driver_info).
RUN uv pip install --python /app/.venv/bin/python --no-deps cognee-community-hybrid-adapter-falkor \
    && uv pip install --python /app/.venv/bin/python "redis>=6" falkordb
