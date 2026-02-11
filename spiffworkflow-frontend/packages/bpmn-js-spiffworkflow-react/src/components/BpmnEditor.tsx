import BpmnModeler from 'bpmn-js/lib/Modeler';
import BpmnViewer from 'bpmn-js/lib/Viewer';
import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
  // @ts-expect-error TS(7016) FIXME: Could not find a declaration file
} from 'bpmn-js-properties-panel';
// @ts-expect-error TS(7016) FIXME: Could not find a declaration file
import CliModule from 'bpmn-js-cli';

// @ts-expect-error TS(7016) FIXME: Could not find a declaration file
import DmnModeler from 'dmn-js/lib/Modeler';
import {
  DmnPropertiesPanelModule,
  DmnPropertiesProviderModule,
  // @ts-expect-error TS(7016) FIXME: Could not find a declaration file
} from 'dmn-js-properties-panel';

import React, {
  useEffect,
  useState,
  useCallback,
  forwardRef,
  useImperativeHandle,
  useRef,
  useId,
} from 'react';

import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';
import 'bpmn-js/dist/assets/bpmn-js.css';

import 'dmn-js/dist/assets/diagram-js.css';
import 'dmn-js/dist/assets/dmn-js-decision-table-controls.css';
import 'dmn-js/dist/assets/dmn-js-decision-table.css';
import 'dmn-js/dist/assets/dmn-js-drd.css';
import 'dmn-js/dist/assets/dmn-js-literal-expression.css';
import 'dmn-js/dist/assets/dmn-js-shared.css';
import 'dmn-js/dist/assets/dmn-font/css/dmn-embedded.css';
import 'dmn-js-properties-panel/dist/assets/properties-panel.css';

// @ts-expect-error TS(7016) FIXME
import spiffworkflow from 'bpmn-js-spiffworkflow/app/spiffworkflow';
import 'bpmn-js-spiffworkflow/app/css/app.css';

import spiffModdleExtension from 'bpmn-js-spiffworkflow/app/spiffworkflow/moddle/spiffworkflow.json';

import KeyboardMoveModule from 'diagram-js/lib/navigation/keyboard-move';
import MoveCanvasModule from 'diagram-js/lib/navigation/movecanvas';
import ZoomScrollModule from 'diagram-js/lib/navigation/zoomscroll';

import '../styles/bpmn-js-properties-panel.css';

import { BpmnEditorProps, BasicTask } from '../types';
import {
  getBpmnProcessIdentifiers,
  convertSvgElementToHtmlString,
  makeid,
  checkTaskCanBeHighlighted,
  taskIsMultiInstanceChild,
} from '../utils/bpmnHelpers';

import {
  BpmnJsScriptIcon,
  CallActivityNavigateArrowUp,
} from '../icons/SvgIcons';

const FitViewport = 'fit-viewport';

export interface BpmnEditorRef {
  getXML: () => Promise<string>;
  zoom: (amount: number) => void;
  getModeler: () => any;
}

export type TaskMetadataItem =
  | string
  | { name: string; label?: string; description?: string };

const DEFAULT_TASK_METADATA_KEYS: TaskMetadataItem[] = [];

export interface BpmnEditorInternalProps extends BpmnEditorProps {
  taskMetadataKeys?: TaskMetadataItem[] | null;
}

const BpmnEditor = forwardRef<BpmnEditorRef, BpmnEditorInternalProps>(
  (
    {
      apiService,
      modifiedProcessModelId,
      diagramType,
      diagramXML,
      fileName,
      tasks,
      url,
      taskMetadataKeys = DEFAULT_TASK_METADATA_KEYS,
      onCallActivityOverlayClick,
      onDataStoresRequested,
      onDmnFilesRequested,
      onElementClick,
      onElementsChanged,
      onJsonSchemaFilesRequested,
      onLaunchBpmnEditor,
      onLaunchDmnEditor,
      onLaunchJsonSchemaEditor,
      onLaunchMarkdownEditor,
      onLaunchScriptEditor,
      onLaunchMessageEditor,
      onMessagesRequested,
      onSearchProcessModels,
      onServiceTasksRequested,
    },
    ref,
  ) => {
    const instanceId = useId().replace(/:/g, '-');
    const containerRef = useRef<HTMLDivElement>(null);
    const [diagramXMLString, setDiagramXMLString] = useState('');
    const [diagramModelerState, setDiagramModelerState] = useState<any>(null);
    const [performingXmlUpdates, setPerformingXmlUpdates] = useState(false);
    const diagramFetchedRef = useRef(false);
    const previousDiagramModelerRef = useRef<any>(null);
    const callbacksRef = useRef({
      onCallActivityOverlayClick,
      onDataStoresRequested,
      onDmnFilesRequested,
      onElementClick,
      onElementsChanged,
      onJsonSchemaFilesRequested,
      onLaunchBpmnEditor,
      onLaunchDmnEditor,
      onLaunchJsonSchemaEditor,
      onLaunchMarkdownEditor,
      onLaunchScriptEditor,
      onLaunchMessageEditor,
      onMessagesRequested,
      onSearchProcessModels,
      onServiceTasksRequested,
    });

    // Update callbacks ref when callbacks change
    useEffect(() => {
      callbacksRef.current = {
        onCallActivityOverlayClick,
        onDataStoresRequested,
        onDmnFilesRequested,
        onElementClick,
        onElementsChanged,
        onJsonSchemaFilesRequested,
        onLaunchBpmnEditor,
        onLaunchDmnEditor,
        onLaunchJsonSchemaEditor,
        onLaunchMarkdownEditor,
        onLaunchScriptEditor,
        onLaunchMessageEditor,
        onMessagesRequested,
        onSearchProcessModels,
        onServiceTasksRequested,
      };
    }, [
      onCallActivityOverlayClick,
      onDataStoresRequested,
      onDmnFilesRequested,
      onElementClick,
      onElementsChanged,
      onJsonSchemaFilesRequested,
      onLaunchBpmnEditor,
      onLaunchDmnEditor,
      onLaunchJsonSchemaEditor,
      onLaunchMarkdownEditor,
      onLaunchScriptEditor,
      onLaunchMessageEditor,
      onMessagesRequested,
      onSearchProcessModels,
      onServiceTasksRequested,
    ]);

    const fitViewportWithPaletteOffset = (canvas: any) => {
      const container = canvas?._container;
      if (
        container &&
        container.clientWidth > 0 &&
        container.clientHeight > 0
      ) {
        canvas.zoom(FitViewport, 'auto');
      }

      try {
        const wrapper = container?.closest('.bpmn-js-container') || container;
        const palette =
          wrapper?.querySelector('.djs-palette') ||
          document.querySelector('.djs-palette');
        if (!palette || !canvas?.viewbox || !canvas?.scroll) {
          return;
        }
        const paletteRect = palette.getBoundingClientRect();
        const overlapWidth = Math.max(0, paletteRect.width);
        if (!overlapWidth) {
          return;
        }
        const viewbox = canvas.viewbox();
        const inner = viewbox?.inner;
        const outer = viewbox?.outer;
        const scale = viewbox?.scale || 1;
        if (
          !inner ||
          !outer ||
          !Number.isFinite(scale) ||
          scale <= 0 ||
          inner.width <= 0 ||
          inner.height <= 0
        ) {
          return;
        }

        // just enough to keep the first element off the left palette
        const padding = 10;

        const desiredLeftPadding = overlapWidth + padding;
        const leftPaddingPx = (inner.x - viewbox.x) * scale;
        const rightPaddingPx =
          (viewbox.x + viewbox.width - (inner.x + inner.width)) * scale;

        let deltaPx = desiredLeftPadding - leftPaddingPx;
        if (deltaPx <= 0) {
          return;
        }

        const maxShiftRight = rightPaddingPx - padding;
        if (maxShiftRight > 0) {
          deltaPx = Math.min(deltaPx, maxShiftRight);
          if (Math.abs(deltaPx) < 0.5) {
            return;
          }
          canvas.viewbox({
            ...viewbox,
            x: viewbox.x - deltaPx / scale,
          });
          return;
        }

        const availableWidth = Math.max(
          0,
          outer.width - overlapWidth - padding * 2,
        );
        const availableHeight = Math.max(0, outer.height - padding * 2);
        if (!availableWidth || !availableHeight) {
          return;
        }

        const targetScale = Math.min(
          scale,
          availableWidth / inner.width,
          availableHeight / inner.height,
        );
        if (!Number.isFinite(targetScale) || targetScale <= 0) {
          return;
        }

        const viewboxWidth = outer.width / targetScale;
        const viewboxHeight = outer.height / targetScale;
        const availableWidthSvg = (outer.width - overlapWidth) / targetScale;
        const offsetXSvg = (overlapWidth + padding) / targetScale;
        const centerX = inner.x + inner.width / 2;
        const centerY = inner.y + inner.height / 2;
        const x = centerX - offsetXSvg - availableWidthSvg / 2;
        const y = centerY - viewboxHeight / 2;
        canvas.viewbox({
          x,
          y,
          width: viewboxWidth,
          height: viewboxHeight,
        });
      } catch (error) {
        console.warn('Failed to offset fit zoom:', error);
      }
    };

    const zoom = useCallback(
      (amount: number) => {
        if (diagramModelerState) {
          let modeler = diagramModelerState as any;
          if (diagramType === 'dmn') {
            modeler = (diagramModelerState as any).getActiveViewer();
          }
          if (modeler) {
            try {
              if (amount === 0) {
                const canvas = modeler.get('canvas');
                fitViewportWithPaletteOffset(canvas);
              } else {
                modeler.get('zoomScroll').stepZoom(amount);
              }
            } catch (error) {
              console.warn('Failed to zoom:', error);
            }
          }
        }
      },
      [diagramModelerState, diagramType],
    );

    // Expose methods to parent via ref
    useImperativeHandle(ref, () => ({
      getXML: async () => {
        if (diagramModelerState) {
          const result = await diagramModelerState.saveXML({
            format: true,
          });
          return result.xml;
        }
        return '';
      },
      zoom,
      getModeler: () => diagramModelerState,
    }));

    /* This restores unresolved references that bpmn-js removes */
    const fixUnresolvedReferences = (diagramModelerToUse: any): null => {
      diagramModelerToUse.on('import.parse.complete', (event: any) => {
        if (!event.references) {
          return;
        }
        const refs = event.references.filter(
          (r: any) =>
            r.property === 'bpmn:loopDataInputRef' ||
            r.property === 'bpmn:loopDataOutputRef',
        );

        const desc =
          diagramModelerToUse._moddle.registry.getEffectiveDescriptor(
            'bpmn:ItemAwareElement',
          );
        refs.forEach((ref: any) => {
          const props = {
            id: ref.id,
            name: typeof ref.name === 'undefined' ? ref.id : ref.name,
          };
          const elem = diagramModelerToUse._moddle.create(desc, props);
          elem.$parent = ref.element;
          ref.element.set(ref.property, elem);
        });
      });
      return null;
    };

    // Initialize the modeler
    useEffect(() => {
      let canvasClass = 'diagram-editor-canvas';
      if (diagramType === 'readonly') {
        canvasClass = 'diagram-viewer-canvas';
      }

      const temp = document.createElement('template');
      const canvasId = `canvas-${instanceId}`;
      const panelId: string =
        diagramType === 'readonly'
          ? `hidden-properties-panel-${instanceId}`
          : `js-properties-panel-${instanceId}`;
      temp.innerHTML = `
      <div class="bpmn-properties-content with-diagram bpmn-js-container" id="js-drop-zone-${instanceId}">
        <div class="canvas ${canvasClass}" id="${canvasId}"></div>
        <div class="properties-panel-parent" id="${panelId}"></div>
      </div>
    `;
      const frag = temp.content;

      const diagramContainerElement = containerRef.current;
      if (diagramContainerElement) {
        diagramContainerElement.innerHTML = '';
        diagramContainerElement.appendChild(frag);
      }

      let diagramModeler: any = null;

      if (diagramType === 'bpmn') {
        diagramModeler = new BpmnModeler({
          container: `#${canvasId}`,
          propertiesPanel: {
            parent: `#${panelId}`,
          },
          additionalModules: [
            spiffworkflow,
            BpmnPropertiesPanelModule,
            BpmnPropertiesProviderModule,
            ZoomScrollModule,
            CliModule,
          ],
          cli: {
            bindTo: 'cli',
          },
          moddleExtensions: {
            spiffworkflow: spiffModdleExtension,
          },
        });
      } else if (diagramType === 'dmn') {
        diagramModeler = new DmnModeler({
          container: `#${canvasId}`,
          drd: {
            propertiesPanel: {
              parent: `#${panelId}`,
            },
            additionalModules: [
              DmnPropertiesPanelModule,
              DmnPropertiesProviderModule,
              ZoomScrollModule,
            ],
          },
        });
      } else if (diagramType === 'readonly') {
        diagramModeler = new BpmnViewer({
          container: `#${canvasId}`,
          additionalModules: [
            KeyboardMoveModule,
            MoveCanvasModule,
            ZoomScrollModule,
          ],
        });
      }

      function handleLaunchScriptEditor(
        element: any,
        script: string,
        scriptType: string,
        eventBus: any,
      ) {
        if (callbacksRef.current.onLaunchScriptEditor) {
          setPerformingXmlUpdates(true);
          const modeling = diagramModeler.get('modeling');
          callbacksRef.current.onLaunchScriptEditor(element, script, scriptType, eventBus, modeling);
        }
      }

      function handleLaunchMarkdownEditor(
        element: any,
        value: string,
        eventBus: any,
      ) {
        if (callbacksRef.current.onLaunchMarkdownEditor) {
          setPerformingXmlUpdates(true);
          callbacksRef.current.onLaunchMarkdownEditor(element, value, eventBus);
        }
      }

      function handleElementClick(event: any) {
        if (callbacksRef.current.onElementClick) {
          const canvas = diagramModeler.get('canvas');
          const bpmnProcessIdentifiers = getBpmnProcessIdentifiers(
            canvas.getRootElement(),
          );
          callbacksRef.current.onElementClick(event.element, bpmnProcessIdentifiers);
        }
      }

      function handleServiceTasksRequested(event: any) {
        if (callbacksRef.current.onServiceTasksRequested) {
          callbacksRef.current.onServiceTasksRequested(event);
        }
      }

      function handleDataStoresRequested(event: any) {
        if (callbacksRef.current.onDataStoresRequested) {
          callbacksRef.current.onDataStoresRequested(event);
        }
      }

      function createPrePostScriptOverlay(event: any) {
        if (event.element && event.element.type !== 'bpmn:ScriptTask') {
          const preScript =
            event.element.businessObject.extensionElements?.values?.find(
              (extension: any) => extension.$type === 'spiffworkflow:PreScript',
            );
          const postScript =
            event.element.businessObject.extensionElements?.values?.find(
              (extension: any) =>
                extension.$type === 'spiffworkflow:PostScript',
            );
          const overlays = diagramModeler.get('overlays');
          const scriptIcon = convertSvgElementToHtmlString(
            <BpmnJsScriptIcon />,
          );

          if (preScript?.value) {
            overlays.add(event.element.id, {
              position: {
                bottom: 25,
                left: 0,
              },
              html: scriptIcon,
            });
          }
          if (postScript?.value) {
            overlays.add(event.element.id, {
              position: {
                bottom: 25,
                right: 25,
              },
              html: scriptIcon,
            });
          }
        }
      }

      setDiagramModelerState(diagramModeler);

      if (diagramType !== 'readonly') {
        diagramModeler.on('shape.added', (event: any) => {
          createPrePostScriptOverlay(event);
        });
      }

      const onMetadataRequested = (event: any) => {
        event.eventBus.fire('spiff.task_metadata_keys.returned', {
          keys: taskMetadataKeys,
        });
      };

      diagramModeler.on(
        'spiff.task_metadata_keys.requested',
        onMetadataRequested,
      );

      diagramModeler.on('spiff.script.edit', (event: any) => {
        const { error, element, scriptType, script, eventBus } = event;
        if (error) {
          console.error(error);
        }
        handleLaunchScriptEditor(element, script, scriptType, eventBus);
      });

      diagramModeler.on('spiff.markdown.edit', (event: any) => {
        const { error, element, value, eventBus } = event;
        if (error) {
          console.error(error);
        }
        handleLaunchMarkdownEditor(element, value, eventBus);
      });

      diagramModeler.on('spiff.callactivity.edit', (event: any) => {
        if (callbacksRef.current.onLaunchBpmnEditor) {
          callbacksRef.current.onLaunchBpmnEditor(event.processId);
        }
      });

      diagramModeler.on('spiff.file.edit', (event: any) => {
        const { error, element, value, eventBus } = event;
        if (error) {
          console.error(error);
        }
        if (callbacksRef.current.onLaunchJsonSchemaEditor) {
          callbacksRef.current.onLaunchJsonSchemaEditor(element, value, eventBus);
        }
      });

      diagramModeler.on('spiff.dmn.edit', (event: any) => {
        if (callbacksRef.current.onLaunchDmnEditor) {
          callbacksRef.current.onLaunchDmnEditor(event.value);
        }
      });

      diagramModeler.on('element.click', (element: any) => {
        handleElementClick(element);
      });

      diagramModeler.on('elements.changed', (event: any) => {
        if (callbacksRef.current.onElementsChanged) {
          callbacksRef.current.onElementsChanged(event);
        }
      });

      diagramModeler.on('spiff.service_tasks.requested', (event: any) => {
        handleServiceTasksRequested(event);
      });

      diagramModeler.on('spiff.data_stores.requested', (event: any) => {
        handleDataStoresRequested(event);
      });

      diagramModeler.on('spiff.json_schema_files.requested', (event: any) => {
        if (callbacksRef.current.onJsonSchemaFilesRequested) {
          callbacksRef.current.onJsonSchemaFilesRequested(event);
        }
      });

      diagramModeler.on('spiff.dmn_files.requested', (event: any) => {
        if (callbacksRef.current.onDmnFilesRequested) {
          callbacksRef.current.onDmnFilesRequested(event);
        }
      });

      diagramModeler.on('spiff.messages.requested', (event: any) => {
        if (callbacksRef.current.onMessagesRequested) {
          callbacksRef.current.onMessagesRequested(event);
        }
      });

      diagramModeler.on('spiff.callactivity.search', (event: any) => {
        if (callbacksRef.current.onSearchProcessModels) {
          callbacksRef.current.onSearchProcessModels(event.value, event.eventBus, event.element);
        }
      });

      diagramModeler.on('spiff.message.edit', (event: any) => {
        if (callbacksRef.current.onLaunchMessageEditor) {
          callbacksRef.current.onLaunchMessageEditor(event);
        }
      });

      // Register the import.parse.complete handler before any importXML calls
      if (diagramType !== 'dmn') {
        fixUnresolvedReferences(diagramModeler);
      }

      // Cleanup: destroy the modeler when component unmounts or when we need a new modeler
      return () => {
        if (diagramModeler) {
          diagramModeler.destroy();
        }
      };
    }, [diagramType, taskMetadataKeys]);

    // Display the diagram
    useEffect(() => {
      if (!diagramXMLString || !diagramModelerState) {
        return;
      }

      // FIXME: This prints unnecessary errors to the console when navigating to call activities.
      // This probably means there's a state or refresh issue going on although it doesn't cause an actual issue.
      diagramModelerState.importXML(diagramXMLString).catch((error: any) => {
        console.error('Failed to import diagram XML:', error);
      });

      // Zoom to fit after a short delay to ensure canvas is rendered
      const timeoutId = window.setTimeout(() => {
        try {
          let modeler = diagramModelerState;
          if (diagramType === 'dmn') {
            modeler = diagramModelerState.getActiveViewer();
          }
          if (modeler) {
            const canvas = modeler.get('canvas');
            // Check if canvas has valid dimensions before zooming
            fitViewportWithPaletteOffset(canvas);
          }
        } catch (error) {
          console.warn('Failed to zoom canvas:', error);
        }
      }, 100);

      return () => {
        clearTimeout(timeoutId);
      };
    }, [diagramXMLString, diagramModelerState, diagramType]);

    // Respond to upstream diagram XML changes (e.g., navigation between files)
    useEffect(() => {
      if (!diagramXML || !diagramModelerState) {
        return;
      }
      setDiagramXMLString(diagramXML);
    }, [diagramXML, diagramModelerState]);

    // Import done operations
    useEffect(() => {
      if (!diagramModelerState) {
        return undefined;
      }

      // Check if modeler instance changed
      const modelerChanged =
        previousDiagramModelerRef.current !== diagramModelerState;

      // Reset state when modeler instance actually changes
      if (modelerChanged) {
        diagramFetchedRef.current = false;
        previousDiagramModelerRef.current = diagramModelerState;
        setPerformingXmlUpdates(false);
      }

      if (performingXmlUpdates) {
        return undefined;
      }

      // Early return if already initialized (prevents re-fetch on tasks/other deps changes)
      if (diagramFetchedRef.current) {
        return undefined;
      }

      function handleError(err: any) {
        console.error('ERROR:', err);
      }

      function highlightBpmnIoElement(
        canvas: any,
        task: BasicTask,
        bpmnIoClassName: string,
        bpmnProcessIdentifiers: string[],
      ) {
        if (checkTaskCanBeHighlighted(task)) {
          try {
            if (
              bpmnProcessIdentifiers.includes(
                task.bpmn_process_definition_identifier,
              )
            ) {
              canvas.addMarker(task.bpmn_identifier, bpmnIoClassName);
            }
          } catch (bpmnIoError: any) {
            if (
              bpmnIoError.message !==
              "Cannot read properties of undefined (reading 'id')"
            ) {
              throw bpmnIoError;
            }
          }
        }
      }

      function addOverlayOnCallActivity(
        task: BasicTask,
        bpmnProcessIdentifiers: string[],
      ) {
        if (
          taskIsMultiInstanceChild(task) ||
          !callbacksRef.current.onCallActivityOverlayClick ||
          diagramType !== 'readonly' ||
          !diagramModelerState
        ) {
          return;
        }
        function domify(htmlString: string) {
          const template = document.createElement('template');
          template.innerHTML = htmlString.trim();
          return template.content.firstChild;
        }
        const createCallActivityOverlay = () => {
          const overlays = diagramModelerState.get('overlays');
          const icon = convertSvgElementToHtmlString(
            <CallActivityNavigateArrowUp />,
          );
          const button: any = domify(
            `<button class="bjs-drilldown">${icon}</button>`,
          );
          button.addEventListener('click', (newEvent: any) => {
            callbacksRef.current.onCallActivityOverlayClick!(task, newEvent);
          });
          button.addEventListener('auxclick', (newEvent: any) => {
            callbacksRef.current.onCallActivityOverlayClick!(task, newEvent);
          });
          overlays.add(task.bpmn_identifier, 'drilldown', {
            position: {
              bottom: -10,
              right: -8,
            },
            html: button,
          });
        };
        try {
          if (
            bpmnProcessIdentifiers.includes(
              task.bpmn_process_definition_identifier,
            )
          ) {
            createCallActivityOverlay();
          }
        } catch (bpmnIoError: any) {
          if (
            bpmnIoError.message !==
            "Cannot read properties of undefined (reading 'id')"
          ) {
            throw bpmnIoError;
          }
        }
      }

      function onImportDone(event: any) {
        const { error } = event;

        if (error) {
          handleError(error);
          return;
        }

        if (diagramType === 'dmn') {
          return;
        }

        const canvas = diagramModelerState.get('canvas');
        // Check if canvas has valid dimensions before zooming
        try {
          fitViewportWithPaletteOffset(canvas);
        } catch (error) {
          console.warn('Failed to zoom canvas on import:', error);
        }

        if (tasks) {
          const bpmnProcessIdentifiers = getBpmnProcessIdentifiers(
            canvas.getRootElement(),
          );
          tasks.forEach((task: BasicTask) => {
            let className = '';
            if (task.state === 'COMPLETED') {
              className = 'completed-task-highlight';
            } else if (['READY', 'WAITING', 'STARTED'].includes(task.state)) {
              className = 'active-task-highlight';
            } else if (task.state === 'CANCELLED') {
              className = 'cancelled-task-highlight';
            } else if (task.state === 'ERROR') {
              className = 'errored-task-highlight';
            }
            if (className) {
              highlightBpmnIoElement(
                canvas,
                task,
                className,
                bpmnProcessIdentifiers,
              );
            }
            if (
              task.typename === 'CallActivity' &&
              !['FUTURE', 'LIKELY', 'MAYBE'].includes(task.state)
            ) {
              addOverlayOnCallActivity(task, bpmnProcessIdentifiers);
            }
          });
        }
      }

      function dmnTextHandler(text: string) {
        const decisionId = `decision_${makeid(7)}`;
        const newText = text.replaceAll('{{DECISION_ID}}', decisionId);
        setDiagramXMLString(newText);
      }

      function bpmnTextHandler(text: string) {
        const processId = `Process_${makeid(7)}`;
        const newText = text.replaceAll('{{PROCESS_ID}}', processId);
        setDiagramXMLString(newText);
      }

      async function fetchDiagramFromURL(
        urlToUse: string,
        textHandler?: (text: string) => void,
      ) {
        try {
          const text = await apiService.loadDiagramTemplate(urlToUse);
          if (textHandler) {
            textHandler(text);
          } else {
            setDiagramXMLString(text);
          }
        } catch (err) {
          handleError(err);
        }
      }

      async function fetchDiagramFromJsonAPI() {
        try {
          const result = await apiService.loadDiagramFile(
            modifiedProcessModelId,
            fileName!,
          );
          setDiagramXMLString(result.file_contents);
        } catch (err) {
          handleError(err);
        }
      }

      (diagramModelerState as any).on('import.done', onImportDone);

      // Mark that we've initialized the fetch logic
      diagramFetchedRef.current = true;

      if (diagramXML) {
        setDiagramXMLString(diagramXML);
      } else if (url) {
        fetchDiagramFromURL(url);
      } else if (fileName) {
        fetchDiagramFromJsonAPI();
      } else {
        let newDiagramFileName = 'new_bpmn_diagram.bpmn';
        let textHandler = bpmnTextHandler;
        if (diagramType === 'dmn') {
          newDiagramFileName = 'new_dmn_diagram.dmn';
          textHandler = dmnTextHandler;
        }
        fetchDiagramFromURL(newDiagramFileName, textHandler);
      }

      return () => {
        (diagramModelerState as any).off('import.done', onImportDone);
      };
    }, [
      apiService,
      diagramModelerState,
      diagramType,
      diagramXML,
      fileName,
      performingXmlUpdates,
      modifiedProcessModelId,
      tasks,
      url,
    ]);

    // The component only renders the container - the actual diagram is rendered by bpmn-js
    return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
  },
);

BpmnEditor.displayName = 'BpmnEditor';

export default BpmnEditor;
