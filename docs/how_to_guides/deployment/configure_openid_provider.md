# Configure an OpenID Provider

SpiffWorkflow supports authentication via OpenID Connect (OIDC) providers.
This guide covers the general configuration options available for integrating with any OpenID provider.

## Environment Variables

All OpenID configuration is done through environment variables.

### Basic OpenID Configuration

```bash
# Core OpenID settings
SPIFFWORKFLOW_BACKEND_AUTHENTICATION_DISABLED=false
SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL=<your_openid_server_url>
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID=<your_client_id>
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY=<your_client_secret>

# OpenID scopes (default: "openid,profile,email")
SPIFFWORKFLOW_BACKEND_OPEN_ID_SCOPES="openid,profile,email"
```

### Advanced Configuration

```bash
# Group management
SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS=false
# Token claim containing a list of group identifiers (default: groups)
SPIFFWORKFLOW_BACKEND_OPEN_ID_GROUPS_CLAIM=groups

# Token validation settings
SPIFFWORKFLOW_BACKEND_OPEN_ID_VERIFY_IAT=true
SPIFFWORKFLOW_BACKEND_OPEN_ID_VERIFY_NBF=true
SPIFFWORKFLOW_BACKEND_OPEN_ID_VERIFY_AZP=true
SPIFFWORKFLOW_BACKEND_OPEN_ID_LEEWAY=5

# Additional valid issuers (comma-separated)
SPIFFWORKFLOW_BACKEND_OPEN_ID_ADDITIONAL_VALID_ISSUERS=<additional_issuers>

# Additional valid client IDs (comma-separated)
SPIFFWORKFLOW_BACKEND_OPEN_ID_ADDITIONAL_VALID_CLIENT_IDS=<additional_client_ids>

# API audiences accepted in OAuth access tokens (comma-separated)
SPIFFWORKFLOW_BACKEND_OPEN_ID_ACCESS_TOKEN_AUDIENCES=<api_audience>

# Optional RFC 8707 resource indicator added to authorization requests
SPIFFWORKFLOW_BACKEND_OPEN_ID_AUTHORIZATION_RESOURCE=<api_audience>

# Tenant-specific fields (comma-separated, max 3)
SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS=<field1,field2,field3>

# Internal URL configuration
SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_INTERNAL_URL=<internal_url>
SPIFFWORKFLOW_BACKEND_OPEN_ID_INTERNAL_URL_IS_VALID_ISSUER=false
```

When OpenID is authoritative, Arena synchronizes the user's memberships from
the configured claim each time the user signs in. A missing or empty claim
removes memberships that are not also assigned by the permissions file or the
default user group. Amazon Cognito names this claim `cognito:groups`, so use:

```bash
SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS=true
SPIFFWORKFLOW_BACKEND_OPEN_ID_GROUPS_CLAIM=cognito:groups
```

## Multi-Provider Configuration

SpiffWorkflow also supports multiple authentication providers through the `SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS` environment variable. This allows users to choose from different OpenID providers at login.

The equivalent per-provider settings are `access_token_audiences` and
`authorization_resource`. For example:

```bash
SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS__0__access_token_audiences__0=https://arena.example.com/api
SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS__0__authorization_resource=https://arena.example.com/api
```

ID tokens and access tokens have different audiences. The OIDC client ID is
the expected audience of an ID token returned during login. An access-token
audience identifies the Arena API that will consume the token. Arena validates
these independently.

`authorization_resource` is provider-dependent. Amazon Cognito uses the RFC
8707 `resource` parameter to bind an access token to an API. Keycloak usually
sets the access-token audience with an audience mapper, and Okta custom
authorization servers define it in the authorization-server configuration.

For backward compatibility, configurations without
`access_token_audiences` continue to accept the legacy client-ID and Keycloak
`account` audiences. Configure an explicit API audience when the provider has
been updated to issue one.

## Provider-Specific Guides

For detailed setup instructions with specific providers, see:

- [Configure Azure as an OpenID Provider](configure_azure_as_an_openid_provider.md)
- [Configure Okta as an OpenID Provider](configure_okta_as_an_openid_provider.md)
- [Keycloak Setup](keycloak_setup.md)

## Complete Configuration Reference

For the complete list of all available configuration options and their defaults, refer to:
`spiffworkflow-backend/src/spiffworkflow_backend/config/default.py`

This file contains all environment variables with their default values and documentation comments explaining their purpose.
