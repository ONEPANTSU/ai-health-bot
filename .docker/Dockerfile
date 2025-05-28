FROM python:3.12.7-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

COPY *.json .
COPY alembic.ini alembic.ini
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
COPY .python-version .python-version
RUN uv sync --frozen

COPY .env .env
COPY src src

ENTRYPOINT ["uv", "run"]
CMD ["-m", "src.main"]