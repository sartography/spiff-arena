# File Upload and Markdown Link Display

This guide documents a process in Spiffworkflow where a user uploads a file, the system generates a downloadable markdown link to the file, and then displays that link back to the user in a follow-up task.

This can be used for tasks such as submitting documents, generating downloadable reports, or capturing file inputs for later reference or distribution.

## Process Overview

![File Upload Process](/images/file_upload_process.png)

This process allows a user to upload a file using a form. The uploaded file is converted into a markdown-compatible link by a script, and the link is then shown to the user in a final confirmation task.

Workflow Steps:

- User uploads a file in the initial task.
- A script task converts the file into a markdown download link.
- A confirmation message is displayed with the link.

## Task Configuration Details

### 1. User Task: Example Manual Task
**Type**: User Task  
**Purpose**: Collect a file upload from the user.  
**UI Output**: Presents a file selection form with a "Submit" and "Save and Close" button.

#### JSON Schema (Form Definition)

```json
{
  "title": "Files",
  "type": "object",
  "properties": {
    "file": {
      "type": "string",
      "format": "data-url",
      "title": "Single file"
    }
  }
}
```

- `file`: This property captures a file as a data URL string. When the task is submitted, Arena stores the original bytes separately and replaces the value of `file` with an internal file reference. Keep that reference unchanged in later tasks; it is not a base64-encoded copy of the file.

#### UI Schema

```json
{
  "file": {
    "ui:options": {
      "accept": ".pdf"
    }
  }
}
```

- The `"accept"` attribute can be configured to restrict allowed file types (e.g., ".pdf", ".png", ".jpg").

#### UI Behavior

- Users click "Choose File" and select a document to upload.
- After selection, the file name, type, and size are shown.
- On clicking "Submit", Arena stores the file and passes its internal reference to the next task.
- In read-only or disabled views, saved files appear as a list with download links (when process instance context is available), without upload or removal controls.

**File Upload Step**  
The interface displays the uploaded filename, type, and size before submission.

![File Upload Process](/images/file_upload_process6.png)

### 2. Script Task: Generate Link to File
**Type**: Script Task  
**Purpose**: Convert the uploaded file into a markdown-compatible download link.

#### Script

```python
link = markdown_file_download_link(file)
```

- `file`: This is the stored file reference from the previous task. Generate the link in a script task after the upload task has been submitted.
- `markdown_file_download_link()` is a built-in function that generates a string like:

  ```markdown
  [filename.ext](https://your-server.com/path/to/file)
  ```

- The output is stored in the process variable `link`.

### 3. Manual Task: Display Link to File
**Type**: Manual Task  
**Purpose**: Show a confirmation message to the user with a clickable link.

#### Instructions (Displayed Text)

```
Thanks for uploading a file!  
Here is a link: {{link}}
```

- The `{{link}}` variable is dynamically replaced with the markdown download link generated in the previous step.

**Display Link to File Step**  
This shows a text message with a link: [filename.ext]”  
![File Upload Process](/images/file_upload_process7.png)


Repeat `{{link}}` in the instructions of every follow-up review task. The same link remains usable after progressing to later tasks or reloading the page, subject to the reviewer's existing file-download permissions. It does not make the attachment public.

Do not use the stored `file` value directly as a Markdown or HTML link, image source, or base64 payload. It contains an internal digest marker rather than the original bytes. Decoding it as base64 can produce a corrupt, very small download even though the stored file is intact. Use `markdown_file_download_link(file)` instead.

### Showing the attachment in a follow-up form

A later user task can reuse the `file` property from the JSON schema above and make it read-only:

```json
{
  "file": {
    "ui:readonly": true
  }
}
```

Arena displays stored attachments as download links rather than interpreting their references as local file previews. This also applies when `ui:options.filePreview` is enabled: unsaved files use the normal local preview, while submitted files use the authenticated download endpoint. A stored reference does not contain the original byte count, so Arena does not display a size derived from the digest.

Filenames containing spaces, brackets, semicolons, or non-ASCII characters are supported; the link helper escapes the filename for Markdown. Keep the generated link intact rather than constructing it by splitting the reference yourself.

You can modify the final message formatting to include file size or type if those details are captured.