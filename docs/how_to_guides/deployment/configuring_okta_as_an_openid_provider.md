# Configure Okta as an OpenID Provider
This guide provides steps to configure Okta as an OpenID Provider (alternative to Keycloak) for SpiffWorkflow. 

The setup involves creating an OpenID Connect (OIDC) application, configuring environment variables, and ensuring group information is passed through correctly.  

## **1. Setting Up OpenID Authentication with Okta**

1. Follow the [Okta App Integration Wizard](https://help.okta.com/en-us/content/topics/apps/apps_app_integration_wizard_oidc.htm) to create an **OpenID Connect (OIDC) Web Application**.
   - This step provides you with a **Client ID** and a **Client Secret** key.

2. **Key Requirements**:
   - Obtain the following details:
     - OpenID Server URL
     - Client ID
     - Client Secret Key  

## **2. Configuring Environment Variables in SpiffWorkflow**

Set the following environment variables on your SpiffWorkflow backend server to connect with your Okta instance:

```bash
# OpenID Server URL
SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL=<YOUR_OKTA_ISSUER_URL>

# Client ID and Secret Key from Okta
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID=<YOUR_CLIENT_ID>
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY=<YOUR_CLIENT_SECRET_KEY>

# OpenID Scopes (includes groups)
SPIFFWORKFLOW_BACKEND_OPENID_SCOPE="openid profile email groups"

# Allow OpenID Provider to manage user groups
SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS: true
```

## **3. Adding a Groups Claim for Authorization Server**

To pass group information to SpiffWorkflow, configure the **Groups Claim** for your OpenID Connect client app in Okta.

1. Go to **Admin Console > Applications > Applications**.

2. Select the OpenID Connect client app you created.

3. Navigate to the **Sign On** tab and click **Edit** under the OpenID Connect ID Token section.

4. In the Group claim type section, you can select either **Filter** or **Expression**. For this example, leave **Filter** selected.
In the Group claims filter section, leave the default name groups (or add it if the box is empty), and then add the appropriate filter. For this example, select Matches regex and enter .* to return the user's groups.
For the **Group claims filter**:
    - Leave the default name `groups` or enter it manually and then add the appropriate filter.
    - For this example, Set the filter to `Matches regex` and use `.*` to return all user groups. 
    
    See [Okta Expression Language Group Functions](https://developer.okta.com/docs/reference/okta-expression-language/#group-functions) for more information on expressions.

5. Click **Save**.

6. Click **Back to applications**.

7. Use the **More** dropdown and select **Refresh Application Data** to apply the changes.

📘 **Reference**: [Customize Tokens and Groups Claim](https://developer.okta.com/docs/guides/customize-tokens-groups-claim/main/).

## **4. Passing Through Groups from Active Directory**

If your organization integrates Active Directory (AD) with Okta, Use the following Okta documentation for guidance:  
   [Retrieve AD and Okta Groups in OIDC Claims](https://support.okta.com/help/s/article/Can-we-retrieve-both-Active-Directory-and-Okta-groups-in-OpenID-Connect-claims?language=en_US).

Adjust the configuration to ensure group information is included in the OpenID Connect token passed to SpiffWorkflow.

## **Example Configuration**

For one of our users, the following setup was used to pass group information to SpiffWorkflow:

![image](/images/okta_config.png)

- Environment variables included the OpenID details and group scope.

- Groups were fetched from Active Directory and passed through to SpiffWorkflow using Okta's configuration tools.

📘 For additional details, refer to Okta’s documentation or the SpiffWorkflow team for troubleshooting. 

🔗 **Helpful Links**:  
- [Okta App Integration Wizard](https://help.okta.com/en-us/content/topics/apps/apps_app_integration_wizard_oidc.htm)  
- [Groups Claim Documentation](https://developer.okta.com/docs/guides/customize-tokens-groups-claim/main/)  
- [Active Directory Groups in Okta](https://support.okta.com/help/s/article/Can-we-retrieve-both-Active-Directory-and-Okta-groups-in-OpenID-Connect-claims?language=en_US).  

```{tags} how_to_guide, devops
```
