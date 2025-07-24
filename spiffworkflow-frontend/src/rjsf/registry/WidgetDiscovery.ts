import { widgetRegistry } from './WidgetRegistry';
import { evaluateWidgetCode, withSandbox } from '../sandbox/WidgetSandbox';
import { ExternalWidgetSource, WidgetRegistration } from '../interfaces/CustomWidgetInterfaces';

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
   * Method kept for backward compatibility
   * Instead, we rely on ContainerForExtensions to load widgets
   * @deprecated Use processWidgetFiles instead
   */
  async loadWidgetsFromExtensions(): Promise<void> {
    console.log('loadWidgetsFromExtensions is deprecated - widgets are loaded directly by ContainerForExtensions');
    return Promise.resolve();
  }

  /**
   * Method kept for backward compatibility
   * @deprecated Use processWidgetFiles instead
   */
  async loadWidgetsFromExtension(extensionId: string): Promise<void> {
    console.log(`loadWidgetsFromExtension is deprecated for ${extensionId}`);
    return Promise.resolve();
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

  // These API methods have been removed as we now get widget data directly from ContainerForExtensions

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
 * Note: We don't need to load widgets here anymore as they are loaded by ContainerForExtensions
 */
export async function initializeWidgetDiscovery(): Promise<void> {
  // Widget loading is handled by ContainerForExtensions
  return Promise.resolve();
}