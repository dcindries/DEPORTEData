FROM eclipse-temurin:17-jdk-jammy AS builder

# Paquetes de sistema
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -o Acquire::Retries=5 && \
    apt-get install -y --no-install-recommends --fix-missing \
      ca-certificates curl wget unzip git maven openssh-client \
      python3 python3-pip python3-numpy python3-scipy python3-pandas && \
    rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install "/usr/bin/python" "python" "$(which python3)" 1


# Dependencias Python
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt


# Apache Spark 3.5.5
ENV SPARK_VERSION=3.5.5 \
    HADOOP_VERSION=3 \
    SPARK_HOME=/opt/spark \
    PYTHONHASHSEED=1

RUN set -eux; \
    SPARK_TGZ="spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz"; \
    PRIMARY="https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/${SPARK_TGZ}"; \
    FALLBACK="https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/${SPARK_TGZ}"; \
    (wget -q "${PRIMARY}" -O /tmp/spark.tgz || wget -q "${FALLBACK}" -O /tmp/spark.tgz); \
    mkdir -p /opt/spark; \
    tar -xf /tmp/spark.tgz -C /opt/spark --strip-components=1; \
    rm /tmp/spark.tgz


# JARs vía Maven (hadoop-aws + mysql-connector)
WORKDIR /tmp/maven-build
COPY pom.xml .
RUN mvn -B -q --no-transfer-progress \
        dependency:copy-dependencies \
        -DoutputDirectory=/opt/spark/jars


# Imagen final
FROM builder AS deportedata-backend

ENV PATH="${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}"

WORKDIR /opt/deportedata-backend

COPY app/ ./app/
COPY spark-jobs/ /opt/spark-apps/
COPY start-backend.sh /start-backend.sh
RUN sed -i 's/\r$//g' /start-backend.sh && chmod +x /start-backend.sh

EXPOSE 8000 8001

CMD ["/bin/bash", "/start-backend.sh"]
