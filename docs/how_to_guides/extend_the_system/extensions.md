# Extensions

Extensions in SpiffArena provide a mechanism to augment the software with custom features and functionalities.
By leveraging extensions, users can implement functions or features not present in the standard offering.
This powerful feature ensures adaptability to various business needs, from custom reports to specific user tools.

At a high level:

- Extensions are implemented as process models within the process model repository.
- Configuration for an extension can be found and modified in its `extension_uischema.json` file.
- Access to an extension can be set up via permissions.

![Extensions](/images/Extensions_dashboard.png)

## Getting Started with Extensions

### Environment Variable Activation

To utilize extensions, an environment variable must be set.
This variable activates the extensions feature in the SpiffWorkflow backend:

    SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED=true

By default, SpiffArena will look for extensions in `[SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR]/extensions`, but that can be configured using `SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX`.

### Creating an Extension

After enabling extensions from the backend, you can create extensions in the SpiffArena frontend.
To create your own custom extension, follow these steps:

- Navigate to the process group repository where extensions are to be implemented.

![Extension Process Group](/images/Extension1.png)

- Create a process model in this group. You can give it whatever name you want. Then create a file inside the process model called `extension_uischema.json`. This will control how the extension will work.

![Extension](/images/Extension_UI_schema.png)

As an example, we have created an extension that adds a link to the profile menu in the top right and also adds a new "Support" page to the app so that users of the application know who to talk to if they have issues.
You can find the full example [on GitHub](https://github.com/sartography/sample-process-models/tree/sample-models-1/extensions/support).

With the current `1.0` schema, navigation intent, route overrides, and CSS assets are split apart more cleanly:

- `navigation`: items that appear in the primary nav, user menu, or configuration tabs
- `routes`: app routes that should render extension-defined pages
- `assets.stylesheets`: CSS files to inject globally
- `pages`: the extension page definitions themselves

For example, a nav item that renders an extension page now looks like this:

```json
{
  "version": "1.0",
  "navigation": [
    {
      "label": "Support",
      "location": "user_menu",
      "target": {
        "type": "extension_page",
        "path": "/support"
      }
    }
  ],
  "pages": {
    "/support": {
      "components": [
        {
          "name": "MarkdownRenderer",
          "arguments": {
            "source": "SPIFF_PROCESS_MODEL_FILE:::support-markdown.md"
          }
        }
      ]
    }
  }
}
```

And a direct nav link to an existing app route can now be modeled without a fake extension page:

```json
{
  "version": "1.0",
  "navigation": [
    {
      "label": "Analytics",
      "location": "primary_nav",
      "icon": "analytics",
      "target": {
        "type": "path",
        "path": "/analytics"
      }
    }
  ]
}
```

SpiffArena still supports older `0.1` and `0.2` extension schemas, but `1.0` is the preferred format for new work.

An entirely new application feature with frontend and backend components can be implemented using an extension.
[This TypeScript interface file](https://github.com/sartography/spiff-arena/blob/main/spiffworkflow-frontend/src/extension_ui_schema_interfaces.ts) codifies the configuration of the extension uischema.

To migrate older extension UI schema files, use:

```bash
python3 ./bin/migrate_extension_uischema.py --write ~/sample-process-models/extensions
```

The migrator is a single-file `uv` script and can also print converted output without modifying files:

```bash
python3 ./bin/migrate_extension_uischema.py --stdout path/to/extension_uischema.json
```

## Adding Custom CSS with Extensions

Extensions can include custom CSS files to style their components or even modify global styling. To add custom CSS to your extension:

1. Create a CSS file within your extension process model directory (e.g., `styles.css`)
2. Specify the stylesheet in `assets.stylesheets` in your `extension_uischema.json`:

```json
{
  "version": "1.0",
  "navigation": [
    {
      "label": "Your Extension",
      "location": "primary_nav",
      "target": {
        "type": "extension_page",
        "path": "/your-page"
      }
    }
  ],
  "assets": {
    "stylesheets": [
      {
        "file": "styles.css"
      }
    ]
  },
  "pages": {
    "/your-page": {
      "header": "Your Extension",
      "components": []
    }
  }
}
```

The CSS will be automatically loaded, sanitized for security, and applied when the extension is loaded. The sanitization process removes potentially dangerous CSS constructs to prevent CSS injection attacks.

This feature allows you to:

- Customize the appearance of your extension pages
- Override default site styles when needed

Use specific class names to avoid conflicts with other extensions or the main application.
Be aware that site structure and style may change over time, so try to minimize customization to avoid future breakage.

## Use Cases

If your organization has specific needs not catered to by the standard SpiffArena features, you can use extensions to add those features.

Here are some of the use cases already implemented by our users:

- Implementing a time tracking system
- Creating custom reports tailored to your business metrics
- Incorporating arbitrary content into custom pages using markdown (as in the above example)
- Creating and accessing tailor-made APIs
- Rendering the output of these APIs using Jinja templates and markdown
- Adding custom styling with CSS files

Extensions in SpiffArena offer a robust mechanism to tailor the software to unique business requirements.
When considering an extension, also consider whether the code would be more properly included in the core source code or as a [connector](how_to_build_a_connector) for external system integrations.

Extensions work well with other SpiffArena extensibility features like [Global Scripts](global_scripts), which provide reusable backend logic that can be called from process models. Extensions can leverage global scripts to perform backend operations while providing custom frontend interfaces.

In cases where an extension is appropriate, by following the instructions in this guide, organizations can expand the system's functionality to meet their unique needs.
