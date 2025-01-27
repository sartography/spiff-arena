# Use Custom Process Metadata

This guide will walk you through the steps to create a process model that generates custom metadata using a metadata extraction path and how to query that metadata using process instance filtering.

## Step 1: Define the Process Model

**Create a New Process Model**:

- Navigate to the "Processes" section in SpiffArena.
- Click on "Add a process model" and fill in the required fields as described elsewhere.
- In the process model form, specify the metadata extraction path.
  - This path is used to extract data from your process instances for quick access in searches and perspectives.
  - Example: If you have a script task that sets `great_color = "blue"`, set both the extraction key and extraction path to `great_color`.
- Save the process model.

## Step 2: Start the Process

1. **Initiate the Process**:

   - Navigate to the "Home" section and click on "Start New" to initiate the process.
   - Select the process model you created and start a new instance.

2. **Monitor Process Execution**:
   - Track the progress of the process instance to ensure it completes successfully and actually generates appropriate task data, such as `great_color` or whatever specific data you are looking for.

## Step 3: Query Custom Metadata

1. **Navigate to Process Instances**:

   - Go to the "Process Instances" section to view all instances.

2. **Expose a column for your Custom Metadata attribute**:

   - Use the plus icon to add a column.
   - Select the metadata field you defined in the extraction path and click Save.
   - You should now be able to see your custom metadata as a new column in the process instance report.

3. **View Filtered Results**:
   - You can also filter process instances based on your custom column using the same column options.

By following these steps, you can create a process model that generates custom metadata and efficiently query that metadata using process instance filtering.

```{tags} how_to_guide, building_diagrams
```
