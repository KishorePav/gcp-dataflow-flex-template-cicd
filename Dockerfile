FROM gcr.io/dataflow-templates-base/python312-template-launcher-base:latest

ARG WORKDIR=/template
WORKDIR ${WORKDIR}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline ./pipeline

ENV FLEX_TEMPLATE_PYTHON_PY_FILE="${WORKDIR}/pipeline/main.py"
ENV FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE="${WORKDIR}/requirements.txt"

