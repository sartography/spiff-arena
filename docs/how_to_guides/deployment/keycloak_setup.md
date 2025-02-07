# Keycloak Setup Guide for Clients 

Keycloak is an open-source identity and access management solution that provides authentication, authorization, and user management features. 

This guide outlines the steps to configure Keycloak for a client, including **granting admin privileges** within a realm and **allowing users to log in using Google authentication**.  

## **1. Super Admin Tasks: Allowing Realm User Management**  

To allow user management in a specific **Keycloak realm**, follow these steps:

### **Step 1: Select the Realm in the Keycloak Admin Console**  
Log in to the **Keycloak Admin Console**. Select the realm you wish to allow access to.

![Image](/images/Keycloak_Setup1.png)

### **Step 2: Enable `security-admin-console` for the Realm**  

Navigate to **Clients**.  Search for **security-admin-console**.  Ensure that it is **enabled** for the realm.

![Image](/images/Keycloak_setup2.png)

### **Step 3: Assign Admin Roles to a User**  
To grant a user admin access for adding/managing users:  
- Navigate to **Users** in the left sidebar. Find or create the user who needs admin privileges.  

![Image](/images/Keycloak_setup3.png)

- Open the user’s profile and go to the **Role Mapping** tab.Add the following roles:  
   - `view-users`  
   - `manage-users`  
   
![Image](/images/Keycloak_setup4.png)
- If you want to grant **full admin access**, search for **realm-management** and grant **all permissions** within realm management.

![Image](/images/Keycloak_setup5.png)

### **Step 4: Provide the Admin URL**  
After assigning roles, provide the user with the following URL to access the **Admin Console**:

```
https://keycloak-[CLIENT'S DOMAIN].spiff.works/admin/[REALM_NAME]/console
```

#### **Example:**  
For a client named **Civitos**, the URL would be:  
```
https://keycloak-civitos.spiff.works/admin/spiffworkflow/console/#/spiffworkflow/users
```

## **2. Allowing Everyone from Your Domain to Log into an Instance**  
*(This example covers **Google as an Identity Provider**, but similar steps can be followed for other providers.)*  

### **Step 1: Set Up Google as an Identity Provider**  
1. Go to the [Google Developer Console](https://console.cloud.google.com/).  
2. Select the project associated with Keycloak (**e.g., `spiffdemo-keycloak`**).  
3. In the search bar, type **“Clients”**.  
4. Click on **+ Create Client**.

### **Step 2: Configure the OAuth Client**  
1. Choose **"Web Application"** as the client type.  
2. Enter a meaningful name based on the client, e.g., **"Jons-chess-boards"**.  
3. **Leave "Authorized JavaScript Origins" blank.**  
4. In the **Authorized Redirect URIs** section, add the following:

   ```
   https://[KEYCLOAK-FOR-CLIENT]/realms/[REALM]/broker/google/endpoint
   ```

   Typically, this would look something like:

   ```
   https://keycloak-jons-chess-boards.spiff.works/realms/spiffworkflow/broker/google/endpoint
   ```

5. Save the configuration and copy the **Client ID** and **Client Secret**.

### **Step 3: Add Google as an Identity Provider in Keycloak**  
1. Go to the **Keycloak Admin Console**.  
2. Select the appropriate **Realm**.  
3. Navigate to **Identity Providers** → **Add Provider** → **Google**.  
4. Enter the **Client ID** and **Client Secret** from Google.  
5. Set **First Login Flow** to `first broker login` (or another authentication flow if required).  
6. Click **Save**.

### **Step 4: Test Login**  
- Navigate to the client’s login page and verify that **Google Login** is now an option.  
- Ensure that users from the domain can successfully authenticate using Google.


By following these steps, you can successfully:  
✔ Grant **admin access** to a user for managing the realm.  
✔ Enable **Google-based authentication** for all users in a client’s domain.  

This setup ensures a secure and efficient user authentication process within **Keycloak**, providing administrators with the ability to manage users effectively while allowing users to authenticate seamlessly using Google.  