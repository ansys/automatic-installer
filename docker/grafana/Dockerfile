from grafana/grafana-oss:8.5.4
USER root
COPY  datasources/* /etc/grafana/provisioning/datasources/
COPY  dashboards/*.yaml /etc/grafana/provisioning/dashboards/
COPY  dashboards/definitions/* /var/lib/grafana/dashboards/
RUN chown -R grafana:root  /etc/grafana/
USER grafana
