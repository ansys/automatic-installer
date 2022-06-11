from grafana/grafana-oss:8.5.4
USER root
COPY  datasources/* /etc/grafana/provisioning/datasources
RUN chown -R grafana:root  /etc/grafana/
USER grafana
