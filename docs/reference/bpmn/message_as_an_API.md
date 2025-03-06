# Message as an API

This BPMN process allows remote execution via an API, enabling external systems to trigger and interact with workflows. 

The process listens for a **message event ("popcorn")**, processes the request, and returns the correct price based on the specified popcorn size using a **Decision Model and Notation (DMN) table**.  

This API is useful in cases where business logic (such as pricing rules) needs to be dynamically updated without modifying the API code.  

## **BPMN Process Model Breakdown**  

![image](/images/message_api.png)

### **1. Message Start Event**  
- This event listens for an API request containing a message named **"popcorn"**.  
- The request must contain a `"size"` parameter in the payload (e.g., `"small"`, `"medium"`, or `"large"`).  
- The API can be triggered by sending a POST request to the corresponding message endpoint.  

### **2. Business Rule Task ("Calculate Popcorn Price")**  
![image](/images/DMN_Table_Message_API.png)

- This task **references a DMN Decision Table** that determines the price of popcorn based on the `"size"` parameter in the request.  
- The DMN table acts as a **dynamic pricing logic**, allowing updates to pricing without modifying the BPMN model.  
- The decision table maps `"small"`, `"medium"`, and `"large"` sizes to their respective prices.  

### **3. End Event**  
- After processing the request, the workflow returns the **calculated price** as the API response.  

## **How to Use This API**  

### **Step 1: Generate an API Key**  
1. Click on your **profile icon** in the top right corner.  Select **"API Keys"**.  

![image](/images/API_Key_Navigation.png)

2. Generate a new API key, give it a name, and **save the key** for future use.  

![image](/images/Generate_API_Key.png)   


### **Step 2: Make the API Call**  
You can interact with the BPMN process API using **cURL, Postman, or any HTTP client**.  

#### **API Endpoint**  
```
[BASE_URL]/v1.0/messages/[MESSAGE_NAME]?execution_mode=synchronous
```
- **BASE_URL**: The API root URL (e.g., `https://api.spiffdemo.org`).  
- **MESSAGE_NAME**: The message event name (`"popcorn"`).  
- **execution_mode=synchronous**: Ensures the API waits for the workflow to process and return a response.  

#### **Required Headers**  
```
Spiffworkflow-Api-Key: [YOUR_API_KEY]  
Content-Type: application/json  
```

#### **Example Requests**  

##### **Using cURL**  
```sh
curl \
'https://api.spiffdemo.org/v1.0/messages/popcorn?execution_mode=synchronous' \
-H 'Spiffworkflow-Api-Key: YOUR_API_KEY' \
-H 'Content-Type: application/json' \
-X POST -d '{"size":"large"}'
```

##### **Example JSON Payloads**  
```json
{"size": "small"}
{"size": "medium"}
{"size": "large"}
```

### **Step 3: Understanding the API Response**  
- The API forwards the `"size"` input to the **DMN decision table**.  
- The **decision table returns the corresponding price** based on predefined pricing rules.  
- The response contains the **calculated price**, which is dynamically retrieved from the decision table.  

#### **Example Response**  
```json
{
  "price": 5.99
}
```
(assuming `$5.99` is the price for `"large"` popcorn)  

## **Use Cases**  

### **1. Automating External Interactions**  

A **web application** allows users to select popcorn sizes, and it fetches the latest price dynamically using this API.  

Example: A movie theater's online ordering system uses this API to get real-time pricing for different popcorn sizes.  

### **2. Event-Driven Workflow Triggers**  
External services can send API requests to trigger workflows in response to events.  

Example: A payment gateway calls this API to verify pricing before completing a transaction.  

### **3. Dynamic Business Rules for Microservices**  
Businesses can **update pricing logic without modifying the API code**, making the system more adaptable.  

Example: A sales team modifies the **DMN decision table** to adjust pricing for promotions or discounts.  

By following this guide, you can use messages as an API to integrate external systems and automate business logic dynamically.