import { widgetRegistry } from './WidgetRegistry';
import { evaluateWidgetCode, withSandbox } from '../sandbox/WidgetSandbox';
import { ExternalWidgetSource, WidgetRegistration } from '../interfaces/CustomWidgetInterfaces';
import HttpService from '../../services/HttpService';

/**
 * Interface for widget files processed from extensions
 */
export interface WidgetFile {
  content: string;
  id: string;
  name: string;
  metadata: any;
  processModelId: string;
}

/**
 * Class responsible for discovering and loading widgets from extensions
 */
export class WidgetDiscovery {
  private extensionWidgetCache: Record<string, ExternalWidgetSource> = {};

  /**
   * Loads widgets from all available extensions
   * @returns Promise that resolves when all widgets are loaded
   */
  async loadWidgetsFromExtensions(): Promise<void> {
    try {
      // Make API call to get list of extensions with custom widgets
      const response = await this.fetchExtensionWidgets();
      
      if (!response || !Array.isArray(response.extensions)) {
        console.warn('No extensions with widgets found or invalid response format');
        return;
      }
      
      // Clear existing extension widgets before loading new ones
      widgetRegistry.clearExtensionWidgets();
      
      // Process each extension
      await Promise.all(
        response.extensions.map(ext => this.loadWidgetsFromExtension(ext.id))
      );
      
      console.log(`Loaded ${Object.keys(this.extensionWidgetCache).length} extension widgets`);
    } catch (error) {
      console.error('Error loading widgets from extensions:', error);
    }
  }

  /**
   * Loads widgets from a specific extension
   * @param extensionId The ID of the extension to load widgets from
   * @returns Promise that resolves when all widgets from the extension are loaded
   */
  async loadWidgetsFromExtension(extensionId: string): Promise<void> {
    try {
      // Get list of widget files in this extension
      const widgetFiles = await this.fetchExtensionWidgetFiles(extensionId);
      
      if (!widgetFiles || !Array.isArray(widgetFiles.files)) {
        console.warn(`No widget files found for extension ${extensionId}`);
        return;
      }
      
      // Process each widget file
      await Promise.all(
        widgetFiles.files.map(async (file) => {
          try {
            // Fetch widget source code
            const widgetSource = await this.fetchWidgetSource(extensionId, file.name);
            if (!widgetSource) {
              console.warn(`Failed to load widget source for ${extensionId}/${file.name}`);
              return;
            }
            
            // Cache the widget source
            const cacheKey = `${extensionId}:${file.name}`;
            this.extensionWidgetCache[cacheKey] = widgetSource;
            
            // Evaluate and register widget
            await this.evaluateAndRegisterWidget(widgetSource, extensionId);
          } catch (err) {
            console.error(`Error processing widget ${file.name} from extension ${extensionId}:`, err);
          }
        })
      );
    } catch (error) {
      console.error(`Error loading widgets from extension ${extensionId}:`, error);
    }
  }

  /**
   * Evaluates widget source code and registers it with the registry
   * @param widgetSource The source code and metadata of the widget
   * @param extensionId The ID of the extension this widget belongs to
   */
  private async evaluateAndRegisterWidget(
    widgetSource: ExternalWidgetSource,
    extensionId: string
  ): Promise<void> {
    // Evaluate the widget code in the sandbox
    const widgetComponent = await evaluateWidgetCode(widgetSource.sourceCode);
    
    if (!widgetComponent) {
      console.error(`Failed to evaluate widget code for ${widgetSource.registration.name}`);
      return;
    }
    
    // Wrap the widget component in a sandbox for runtime protection
    const sandboxedWidget = withSandbox(widgetComponent);
    
    // Register the widget with the registry
    const registration: WidgetRegistration = {
      ...widgetSource.registration,
      component: sandboxedWidget,
      source: 'extension',
      extensionId,
    };
    
    widgetRegistry.registerWidget(registration);
    console.log(`Registered widget ${registration.name} from extension ${extensionId}`);
  }

  /**
   * Makes API call to fetch all extensions with custom widgets
   * @returns Promise that resolves with the extension list response
   */
  private async fetchExtensionWidgets(): Promise<any> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: '/extensions-with-custom-widgets',
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  /**
   * Makes API call to fetch widget files for a specific extension
   * @param extensionId The ID of the extension
   * @returns Promise that resolves with the widget files response
   */
  private async fetchExtensionWidgetFiles(extensionId: string): Promise<any> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: `/extension/${extensionId}/widget-files`,
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  /**
   * Makes API call to fetch widget source code
   * @param extensionId The ID of the extension
   * @param fileName The name of the widget file
   * @returns Promise that resolves with the widget source code response
   */
  private async fetchWidgetSource(extensionId: string, fileName: string): Promise<ExternalWidgetSource | null> {
    return new Promise((resolve, reject) => {
      HttpService.makeCallToBackend({
        path: `/extension/${extensionId}/widget-file/${fileName}`,
        successCallback: resolve,
        failureCallback: reject,
      });
    });
  }

  /**
   * Gets a widget from the cache by extension ID and file name
   * @param extensionId The ID of the extension
   * @param fileName The name of the widget file
   * @returns The widget source if found, null otherwise
   */
  getWidgetFromCache(extensionId: string, fileName: string): ExternalWidgetSource | null {
    const cacheKey = `${extensionId}:${fileName}`;
    return this.extensionWidgetCache[cacheKey] || null;
  }
  
  /**
   * Processes widget files directly from the ContainerForExtensions component
   * @param widgetFiles Array of widget files to process
   */
  async processWidgetFiles(widgetFiles: WidgetFile[]): Promise<void> {
    try {
      // Clear existing extension widgets before loading new ones
      widgetRegistry.clearExtensionWidgets();
      
      // Process each widget file
      await Promise.all(
        widgetFiles.map(async (widgetFile) => {
          try {
            // Create external widget source from the file
            const widgetSource: ExternalWidgetSource = {
              sourceCode: widgetFile.content,
              registration: {
                name: widgetFile.name,
                metadata: widgetFile.metadata,
                source: 'extension',
                extensionId: widgetFile.processModelId
              }
            };
            
            // Cache the widget source
            const cacheKey = `${widgetFile.processModelId}:${widgetFile.id}`;
            this.extensionWidgetCache[cacheKey] = widgetSource;
            
            // Evaluate and register widget
            await this.evaluateAndRegisterWidget(widgetSource, widgetFile.processModelId);
          } catch (err) {
            console.error(`Error processing widget ${widgetFile.name}:`, err);
          }
        })
      );
      
      console.log(`Processed ${widgetFiles.length} widget files from extensions`);
    } catch (error) {
      console.error('Error processing widget files:', error);
    }
  }
}

// Singleton instance of the widget discovery class
export const widgetDiscovery = new WidgetDiscovery();

/**
 * Initialize widget discovery system
 * This should be called during application startup
 */
export async function initializeWidgetDiscovery(): Promise<void> {
  await widgetDiscovery.loadWidgetsFromExtensions();
}