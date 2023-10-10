FROM quay.io/keycloak/keycloak:22.0.4 as builder

ENV KEYCLOAK_LOGLEVEL="ALL"
ENV ROOT_LOGLEVEL="ALL"
ENV KC_HEALTH_ENABLED="true"
# ENV KC_METRICS_ENABLED=true
ENV PROXY_ADDRESS_FORWARDING="true"
# ENV KC_HOSTNAME="keycloak.demo.spiffworkflow.org"
# ENV KC_HOSTNAME_URL="https://keycloak.demo.spiffworkflow.org"
ENV KC_FEATURES="token-exchange,admin-fine-grained-authz"
# ENV KC_DB=postgres
# Install custom providers
# RUN curl -sL https://github.com/aerogear/keycloak-metrics-spi/releases/download/2.5.3/keycloak-metrics-spi-2.5.3.jar -o /opt/keycloak/providers/keycloak-metrics-spi-2.5.3.jar
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:22.0.4
COPY --from=builder /opt/keycloak/ /opt/keycloak/
WORKDIR /opt/keycloak

COPY spifftheme /opt/keycloak/themes/spifftheme

# for demonstration purposes only, please make sure to use proper certificates in production instead
# RUN keytool -genkeypair -storepass password -storetype PKCS12 -keyalg RSA -keysize 2048 -dname "CN=server" -alias server -ext "SAN:c=DNS:localhost,IP:127.0.0.1" -keystore conf/server.keystore
# # change these values to point to a running postgres instance
# ENV KC_DB_URL=<DBURL>
# ENV KC_DB_USERNAME=<DBUSERNAME>
# ENV KC_DB_PASSWORD=<DBPASSWORD>
# ENV KC_HOSTNAME=localhost
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
