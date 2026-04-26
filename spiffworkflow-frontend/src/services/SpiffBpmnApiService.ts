/**
 * SpiffWorkflow-specific implementation of BpmnApiService
 * Bridges the bpmn-js-spiffworkflow-react package with the existing HttpService
 */

import { BpmnApiService } from '../../packages/bpmn-js-spiffworkflow-react/src/services/BpmnApiService';
import HttpService from './HttpService';

export class SpiffBpmnApiService implements BpmnApiService {
  async loadDiagramFile(
    modifiedProcessModelId: string,
    fileName: string,
  ): Promise<{ file_contents: string }> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/files/${fileName}`,
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  async saveDiagramFile(
    modifiedProcessModelId: string,
    fileName: string,
    content: string,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/files/${fileName}`,
        httpMethod: 'PUT',
        postBody: { file_contents: content },
        successCallback: () => resolve(),
        failureCallback: reject,
      });
    });
  }

  async loadDiagramTemplate(templateName: string): Promise<string> {
    // Templates are served as static files from the public directory
    const response = await fetch(`/${templateName}`);
    if (!response.ok) {
      throw new Error(`Failed to load template: ${templateName}`);
    }
    return response.text();
  }

  async getServiceTasks(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: '/service-tasks',
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  async getDataStores(processGroupIdentifier?: string): Promise<any[]> {
    const query = processGroupIdentifier
      ? `?upsearch=true&process_group_identifier=${processGroupIdentifier}`
      : '';
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: `/data-stores${query}`,
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  async getMessages(path?: string): Promise<any[]> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: path || '/messages',
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  async getDmnFiles(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: '/dmn-files',
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  async getJsonSchemaFiles(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: '/json-schema-files',
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  async searchProcessModels(query: string): Promise<any[]> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: `/process-models?search=${encodeURIComponent(query)}`,
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  async getProcesses(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: '/processes',
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }
}

// Singleton instance for convenience
export const spiffBpmnApiService = new SpiffBpmnApiService();
