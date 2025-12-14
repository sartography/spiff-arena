/**
 * API Service interface for BPMN Editor
 * Applications can implement this interface to provide their own API integration
 */

export interface BpmnApiService {
  /**
   * Load diagram file from backend
   */
  loadDiagramFile(processModelId: string, fileName: string): Promise<{ file_contents: string }>;

  /**
   * Save diagram file to backend
   */
  saveDiagramFile(processModelId: string, fileName: string, content: string): Promise<void>;

  /**
   * Load static diagram template (for new diagrams)
   */
  loadDiagramTemplate(templateName: string): Promise<string>;

  /**
   * Get service task definitions
   */
  getServiceTasks?(): Promise<any[]>;

  /**
   * Get data store definitions
   */
  getDataStores?(): Promise<any[]>;

  /**
   * Get message definitions
   */
  getMessages?(): Promise<any[]>;

  /**
   * Get DMN file list
   */
  getDmnFiles?(): Promise<any[]>;

  /**
   * Get JSON schema files
   */
  getJsonSchemaFiles?(): Promise<any[]>;

  /**
   * Search process models (for call activities)
   */
  searchProcessModels?(query: string): Promise<any[]>;
}

/**
 * Configuration for API endpoints and behavior
 */
export interface BpmnApiConfig {
  /**
   * Base URL for API calls
   */
  baseUrl?: string;

  /**
   * Custom headers for API requests
   */
  headers?: Record<string, string>;

  /**
   * Custom fetch implementation (for auth, interceptors, etc.)
   */
  fetchFn?: typeof fetch;

  /**
   * Template base URL for loading static templates
   */
  templateBaseUrl?: string;

  /**
   * Error handler for API failures
   */
  onError?: (error: Error) => void;

  /**
   * Handler for unauthorized responses
   */
  onUnauthorized?: () => void;
}

/**
 * Default implementation using standard fetch
 * Applications can extend this or implement BpmnApiService from scratch
 */
export class DefaultBpmnApiService implements BpmnApiService {
  protected config: BpmnApiConfig;

  constructor(config: BpmnApiConfig = {}) {
    this.config = {
      baseUrl: '',
      templateBaseUrl: '/',
      fetchFn: fetch,
      headers: {},
      ...config
    };
  }

  protected async makeRequest(path: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.config.baseUrl}${path}`;
    const fetchFn = this.config.fetchFn || fetch;

    const response = await fetchFn(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...this.config.headers,
        ...options.headers,
      },
    });

    if (response.status === 401 && this.config.onUnauthorized) {
      this.config.onUnauthorized();
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
      if (this.config.onError) {
        this.config.onError(error);
      }
      throw error;
    }

    return response.json();
  }

  async loadDiagramFile(processModelId: string, fileName: string): Promise<{ file_contents: string }> {
    return this.makeRequest(`/process-models/${processModelId}/files/${fileName}`);
  }

  async saveDiagramFile(processModelId: string, fileName: string, content: string): Promise<void> {
    await this.makeRequest(`/process-models/${processModelId}/files/${fileName}`, {
      method: 'PUT',
      body: JSON.stringify({ file_contents: content }),
    });
  }

  async loadDiagramTemplate(templateName: string): Promise<string> {
    const fetchFn = this.config.fetchFn || fetch;
    const response = await fetchFn(`${this.config.templateBaseUrl}${templateName}`);

    if (!response.ok) {
      throw new Error(`Failed to load template: ${templateName}`);
    }

    return response.text();
  }

  async getServiceTasks(): Promise<any[]> {
    return this.makeRequest('/service-tasks');
  }

  async getDataStores(): Promise<any[]> {
    return this.makeRequest('/data-stores');
  }

  async getMessages(): Promise<any[]> {
    return this.makeRequest('/messages');
  }

  async getDmnFiles(): Promise<any[]> {
    return this.makeRequest('/dmn-files');
  }

  async getJsonSchemaFiles(): Promise<any[]> {
    return this.makeRequest('/json-schema-files');
  }

  async searchProcessModels(query: string): Promise<any[]> {
    return this.makeRequest(`/process-models?search=${encodeURIComponent(query)}`);
  }
}

/**
 * SpiffWorkflow-specific implementation
 * This shows how an app would extend the default service
 */
export class SpiffWorkflowApiService extends DefaultBpmnApiService {
  constructor(config: BpmnApiConfig = {}) {
    super({
      baseUrl: '/v1.0',
      templateBaseUrl: '/',
      ...config
    });
  }

  // Override or add SpiffWorkflow-specific methods
  async getServiceTasks(): Promise<any[]> {
    // SpiffWorkflow-specific endpoint structure
    return this.makeRequest('/service-tasks');
  }
}