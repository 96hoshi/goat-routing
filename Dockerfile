FROM python:3.11.4-bookworm
# create directory for the app user
RUN mkdir -p /app
WORKDIR /app/
# Create the app user
#RUN addgroup --system app && adduser --system --group app
# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENVIRONMENT prod
ENV PYTHONPATH "${PYTHONPATH}:."
ENV USE_PYGEOS 0

# Set environment variables for Celery
ENV CELERYD_NODES 1
ENV CELERY_BIN "celery"
ENV CELERYD_CHDIR "/app"
ENV CELERY_APP "src.core.worker"
ENV CELERYD_LOG_FILE "/var/log/celery/%n%I.log"
ENV CELERYD_PID_FILE "/var/run/celery/%n.pid"
ENV CELERYD_USER "root"
ENV CELERYD_GROUP "root"
ENV CELERY_CREATE_DIRS 1
ENV CELERY_RESULT_EXPIRES 120



# Install system dependencies and gdal binaries
RUN apt-get update \
    && apt-get -y install netcat-traditional gcc libpq-dev python3-dev gdal-bin libgdal-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Download Celery daemon
RUN curl -sSL https://raw.githubusercontent.com/celery/celery/master/extra/generic-init.d/celeryd > /etc/init.d/celeryd && \
    chmod +x /etc/init.d/celeryd

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /app/
# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=true

RUN if [ "$INSTALL_DEV" = "true" ]; then poetry install --no-root ; else poetry install --no-root --only main ; fi
COPY . /app

# Run API server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "6000"]
