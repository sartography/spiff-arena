import React from 'react';
import HttpService from '../services/HttpService';
import { modifyProcessModelPath } from '../helpers';

type Props = {
  processGroupId: string;
  processModelId: string;
  onUploadedCallback?: (..._args: any[]) => any;
};

export default class FileInput extends React.Component<Props> {
  fileInput: any;

  processGroupId: any;

  processModelId: any;

  onUploadedCallback: any;

  constructor({ processGroupId, processModelId, onUploadedCallback }: Props) {
    super({ processGroupId, processModelId, onUploadedCallback });
    this.handleSubmit = this.handleSubmit.bind(this);
    this.fileInput = React.createRef();
    this.processGroupId = processGroupId;
    this.processModelId = processModelId;
    this.onUploadedCallback = onUploadedCallback;
  }

  handleSubmit(event: any) {
    event.preventDefault();
    const modifiedProcessModelId = modifyProcessModelPath(
      `${this.processGroupId}/${this.processModelId}`
    );
    const url = `/process-models/${modifiedProcessModelId}/files`;
    const formData = new FormData();
    formData.append('file', this.fileInput.current.files[0]);
    formData.append('fileName', this.fileInput.current.files[0].name);
    HttpService.makeCallToBackend({
      path: url,
      successCallback: this.onUploadedCallback,
      httpMethod: 'POST',
      postBody: formData,
    });
  }

  render() {
    return (
      <form onSubmit={this.handleSubmit}>
        <label>
          Upload file:
          <input type="file" ref={this.fileInput} />
        </label>
        <button type="submit">Submit</button>
      </form>
    );
  }
}
