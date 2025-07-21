# Configure Azure Entra as an OpenID Provider

## Register your app

1. Sign in to the [Microsoft Entra admin center](https://entra.microsoft.com/).
2. Browse to _Applications > App registrations_ using the sidebar.
3. Enter the name of your application, like `spiffworkflow-backend`.
4. Under _supported account types,_ you will likely want "Accounts in this organizational directory only"
5. Skip the redirect URL. We will do that later.
6. Click _Register._
7. In the new view, copy and note the following:
    - _Application (client) ID._ It is your **Client ID.**
    - _Directory (tenant) ID._ This is part of your server URL.
 

### Configure your app

1. Select _Authentication_ from the sidebar.
2. Under _Platform configurations,_ select "+ Add a platform"
3. In the pane that opens, select _Web_.
4. Under _Redirect URIs,_ add `http://localhost:8000/v1.0/login_return`
5. Leave _Front-chanel logout URL_ blank.
6. Leave the checkboxes unchecked under _Implicit grant and hybrid flows._
7. Click _Configure._

### Add additional Redirect URLs

You will need to add more redirect URLs.

Follow these instructions for the following URL patterns:

- `http://localhost:8000/v1.0/login_api_return`
- `https://<domainname>/v1.0/login_return`
- `https://<domainname>/v1.0/login_api_return`

1. Under _Web > Redirect URIs,_ click _Add URI._
2. Type in the URL pattern.

### Create a Client Secret

1. Select _Certificates & Secrets_ from the sidebar.
2. Click _+ New client secret_
3. In the pane that opens, enter a description and expiration, then click _Add._
4. Copy the _Value_ using the icon after the string and note this value. This is your **Client Secret Key.**

### Add groups claim to the token

The basic steps are:

1. Select _Token configuration_ from the sidebar.
2. Select _Add groups claim._
3. Select the group types to return (Security groups, or Directory roles, All groups, and/or Groups assigned to the application)
4. Select _Save._

For more information about these settings read the [Microsoft documentation](https://learn.microsoft.com/en-us/entra/identity-platform/optional-claims?tabs=appui#configure-groups-optional-claims)

## Configure Spiff Workflow

Set the following environment variables on your SpiffWorkflow backend server to connect with your Azure Entra instance:

```bash
# OpenID Server URL
SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL=https://login.microsoftonline.com/<YOUR_DIRECTORY_(TENANT)_ID>

# Client ID and Secret Key from Okta
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID=<YOUR_CLIENT_ID>
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY=<YOUR_CLIENT_SECRET_KEY>

# Additional valid issuers (don't forget the trailing slash)
SPIFFWORKFLOW_BACKEND_OPEN_ID_ADDITIONAL_VALID_ISSUERS: "https://sts.windows.net/<YOUR_DIRECTORY_(TENANT)_ID>/"

# OpenID Scopes (includes groups)
SPIFFWORKFLOW_BACKEND_OPENID_SCOPE="openid profile email groups"

# Allow OpenID Provider to manage user groups
SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS: true
```
