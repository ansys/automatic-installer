from grafana/grafana-oss:8.5.4
USER root
COPY grafana.db /var/lib/grafana/grafana.db
RUN chown grafana:root  /var/lib/grafana/grafana.db
USER grafana
