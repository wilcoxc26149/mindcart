FROM cognee/cognee:1.5.4

COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /usr/local/bin/uv
COPY sitecustomize.py /opt/mindcart/sitecustomize.py
COPY sitecustomize.py /app/.venv/lib/python3.12/site-packages/sitecustomize.py
ENV PYTHONPATH=/opt/mindcart

USER root
# Keep the image's Cognee version; only add the Falkor adapter and a redis
# new enough for falkordb (redis.driver_info).
RUN uv pip install --python /app/.venv/bin/python --no-deps cognee-community-hybrid-adapter-falkor==0.4.0 \
    && uv pip install --python /app/.venv/bin/python redis==8.1.0 falkordb==1.7.1
