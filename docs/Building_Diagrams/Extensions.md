# Extensions

Extensions in SpiffArena provide a mechanism to augment the software with custom features and functionality.
By leveraging extensions, users can implement functions or features not present in the standard offering.
This powerful feature ensures adaptability to various business needs, from custom reports to specific user tools.

Here are some of key aspects of using Extensions:
-   Extensions are implemented within the process model repository.
-   Once an extension is created, it can be made accessible via the top navigation bar.
-   Extensions are universal. Once added, they will be visible to all users and are not user-specific.
-   Configuration for an extensions can be found and modified in its `extension-uischema.json` file.

![Extensions](images/Extensions_dashboard.png)

## Getting Started with Extensions

### Environment Variable Activation

To utilize extensions, an environment variable must be set.
This variable activates the extensions feature in the SpiffWorkflow backend.
Here is the enviromental variable:

    SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED=true

If SpiffWorkflow is being deployed using Docker Compose, add the environment variable under the selected section of your `docker-compose.yml` file as shown in screenshot:

![Enviromental variable](images/Extensions2.png)

### Creating an Extension
After enabling extensions from the backend, you can create extensions in the SpiffArena frontend.
To create your own custom extension, follow these steps:

-   Navigate to the process model repository where extensions are to be implemented.

![Extension Process Group](images/Extension1.png)
    
-   Create the `extension-uischema.json` file. If you want to modify an existing extension, you can change the layout as well in existing models.

![Extension](images/Extension_UI_schema.png)
    
-   To add a new extension with navigation, incorporate the navigation function within this JSON file. For instance, we are taking an example of aggregate metadata extension:

``` json
{
    "navigation_items": [{
        "label": "Aggregate Metadata",
        "route": "/aggregate-metadata"
        }
    ],
    "routes": {
        "/aggregate-metadata": {
            "header": "Aggregate Metdata",
            "api": "aggregate-metadata",
            "form_schema_filename": "we-aggregate-schema.json",
            "form_ui_schema_filename": "we-aggregate-uischema.json",
            "markdown_instruction_filename": "we-aggregate-markdown.md",
            "results_markdown_filename": "we-aggregate-results-markdown.md"
        }
    }
}

```
The provided JSON structure describes configuration for a data aggregation feature with user interface components including navigation.
Here's a breakdown of the key components:

1. `navigation_items`: This is an array containing additional navigation items that should be added to the application. In this case, there's only one item:
   - `"label"`: The label or display text for the navigation item is "Aggregate Metadata".
   - `"route"`: The route or URL associated with the navigation item is "/aggregate-metadata". This indicates that clicking on this navigation item would take the user to this specific path.

2. `routes`: This is an object that defines new routes within the application. In this case, there's only one route defined:
   - `"/aggregate-metadata"`: This is the URL route that corresponds to the previously mentioned navigation item. The details for this route are:
     - `"header"`: The header or title for the page associated with this route is "Aggregate Metadata".
     - `"api"`: This refers to an API endpoint that is used to retrieve or manipulate aggregated metadata.
     - `"form_schema_filename"`: The filename "we-aggregate-schema.json" points to a JSON schema that describes the structure of the data to be submitted through a form on the "Aggregate Metadata" page.
     - `"form_ui_schema_filename"`: The filename "we-aggregate-uischema.json" points to a UI schema that specifies how the form elements on the page should be rendered and arranged.
     - `"markdown_instruction_filename"`: The filename "we-aggregate-markdown.md" points to a Markdown file containing instructions or guidance for the user when interacting with the form on the "Aggregate Metadata" page.
     - `"results_markdown_filename"`: The filename "we-aggregate-results-markdown.md" points to a Markdown file where the results of the aggregation process will be displayed or explained.

This route has associated components such as a header, API endpoint, form schema, form UI schema, instructions in Markdown format, and a results display in Markdown format, all related to the process of aggregating metadata.
An entirely new feature application feature with frontend and backend components can therefore be implemented using an extension in this way.

-   Deploy your changes and ensure the environment variable is activated to see your extensions in the top navigation bar and start adding new features to SpiffArena.

![Extension](images/Agregate_metadata.png)

## Use Cases

If your organization has specific needs not catered to by the standard SpiffArena features, you can use extensions to add those features.  

Here are some of the use cases already implemented by our users:
-   Implementing a time tracking system.
-   Creating custom reports tailored to your business metrics.
-   Incorporating arbitrary content into custom pages using markdown.
-   Creating and accessing tailor-made APIs.
-   Rendering the output of these APIs using jinja templates and markdown.

Extensions in SpiffArena offer a robust mechanism to tailor the software to unique business requirements.
When considering an extension, also consider whether the code would be more properly included in the core source code.
In the cases where an extension is appropriate, by following the instructions in this guide, organizations can expand the system's functionality to meet their unique needs.
