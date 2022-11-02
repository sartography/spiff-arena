/* eslint-disable sonarjs/cognitive-complexity */
// @ts-expect-error TS(7016) FIXME: Could not find a declaration file for module 'bpmn... Remove this comment to see the full error message
import BpmnModeler from 'bpmn-js/lib/Modeler';
// @ts-expect-error TS(7016) FIXME: Could not find a declaration file for module 'bpmn... Remove this comment to see the full error message
import BpmnViewer from 'bpmn-js/lib/Viewer';
import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
  // @ts-expect-error TS(7016) FIXME: Could not find a declaration file for module 'bpmn... Remove this comment to see the full error message
} from 'bpmn-js-properties-panel';

// @ts-expect-error TS(7016) FIXME: Could not find a declaration file for module 'dmn-... Remove this comment to see the full error message
import DmnModeler from 'dmn-js/lib/Modeler';
import {
  DmnPropertiesPanelModule,
  DmnPropertiesProviderModule,
  // @ts-expect-error TS(7016) FIXME: Could not find a declaration file for module 'dmn-... Remove this comment to see the full error message
} from 'dmn-js-properties-panel';

import React, { useRef, useEffect, useState } from 'react';
import Button from 'react-bootstrap/Button';

import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';
import 'bpmn-js-properties-panel/dist/assets/properties-panel.css';
import '../bpmn-js-properties-panel.css';
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

// @ts-expect-error TS(7016) FIXME
import spiffModdleExtension from 'bpmn-js-spiffworkflow/app/spiffworkflow/moddle/spiffworkflow.json';

// @ts-expect-error TS(7016) FIXME
import KeyboardMoveModule from 'diagram-js/lib/navigation/keyboard-move';
// @ts-expect-error TS(7016) FIXME
import MoveCanvasModule from 'diagram-js/lib/navigation/movecanvas';
// @ts-expect-error TS(7016) FIXME
import TouchModule from 'diagram-js/lib/navigation/touch';
// @ts-expect-error TS(7016) FIXME
import ZoomScrollModule from 'diagram-js/lib/navigation/zoomscroll';

import HttpService from '../services/HttpService';

import ButtonWithConfirmation from './ButtonWithConfirmation';
import { makeid } from '../helpers';

type OwnProps = {
  processModelId: string;
  processGroupId: string;
  diagramType: string;
  readyOrWaitingBpmnTaskIds?: string[] | null;
  completedTasksBpmnIds?: string[] | null;
  saveDiagram?: (..._args: any[]) => any;
  onDeleteFile?: (..._args: any[]) => any;
  onSetPrimaryFile?: (..._args: any[]) => any;
  diagramXML?: string | null;
  fileName?: string;
  onLaunchScriptEditor?: (..._args: any[]) => any;
  onElementClick?: (..._args: any[]) => any;
  onServiceTasksRequested?: (..._args: any[]) => any;
  url?: string;
};

// https://codesandbox.io/s/quizzical-lake-szfyo?file=/src/App.js was a handy reference
export default function ReactDiagramEditor({
  processModelId,
  processGroupId,
  diagramType,
  readyOrWaitingBpmnTaskIds,
  completedTasksBpmnIds,
  saveDiagram,
  onDeleteFile,
  onSetPrimaryFile,
  diagramXML,
  fileName,
  onLaunchScriptEditor,
  onElementClick,
  onServiceTasksRequested,
  url,
}: OwnProps) {
  const [diagramXMLString, setDiagramXMLString] = useState('');
  const [diagramModelerState, setDiagramModelerState] = useState(null);
  const [performingXmlUpdates, setPerformingXmlUpdates] = useState(false);

  const alreadyImportedXmlRef = useRef(false);

  useEffect(() => {
    if (diagramModelerState) {
      return;
    }

    let canvasClass = 'diagram-editor-canvas';
    if (diagramType === 'readonly') {
      canvasClass = 'diagram-viewer-canvas';
    }

    const temp = document.createElement('template');
    temp.innerHTML = `
      <div class="content with-diagram" id="js-drop-zone">
        <div class="canvas ${canvasClass}" id="canvas"
                            ></div>
        <div class="properties-panel-parent" id="js-properties-panel"></div>
      </div>
    `;
    const frag = temp.content;

    const diagramContainerElement =
      document.getElementById('diagram-container');
    if (diagramContainerElement) {
      diagramContainerElement.innerHTML = '';
      diagramContainerElement.appendChild(frag);
    }

    let diagramModeler: any = null;

    if (diagramType === 'bpmn') {
      diagramModeler = new BpmnModeler({
        container: '#canvas',
        keyboard: {
          bindTo: document,
        },
        propertiesPanel: {
          parent: '#js-properties-panel',
        },
        additionalModules: [
          spiffworkflow,
          BpmnPropertiesPanelModule,
          BpmnPropertiesProviderModule,
        ],
        moddleExtensions: {
          spiffworkflow: spiffModdleExtension,
        },
      });
    } else if (diagramType === 'dmn') {
      diagramModeler = new DmnModeler({
        container: '#canvas',
        keyboard: {
          bindTo: document,
        },
        drd: {
          propertiesPanel: {
            parent: '#js-properties-panel',
          },
          additionalModules: [
            DmnPropertiesPanelModule,
            DmnPropertiesProviderModule,
          ],
        },
      });
    } else if (diagramType === 'readonly') {
      diagramModeler = new BpmnViewer({
        container: '#canvas',
        keyboard: {
          bindTo: document,
        },

        // taken from the non-modeling components at
        //  bpmn-js/lib/Modeler.js
        additionalModules: [
          KeyboardMoveModule,
          MoveCanvasModule,
          TouchModule,
          ZoomScrollModule,
        ],
      });
    }

    function handleLaunchScriptEditor(
      element: any,
      script: string,
      scriptType: string,
      eventBus: any
    ) {
      if (onLaunchScriptEditor) {
        setPerformingXmlUpdates(true);
        const modeling = diagramModeler.get('modeling');
        onLaunchScriptEditor(element, script, scriptType, eventBus, modeling);
      }
    }

    function handleElementClick(event: any) {
      if (onElementClick) {
        onElementClick(event.element);
      }
    }

    function handleServiceTasksRequested(event: any) {
      if (onServiceTasksRequested) {
        onServiceTasksRequested(event);
      }
    }

    setDiagramModelerState(diagramModeler);

    diagramModeler.on('script.editor.launch', (event: any) => {
      const { error, element, scriptType, script, eventBus } = event;
      if (error) {
        console.log(error);
      }
      handleLaunchScriptEditor(element, script, scriptType, eventBus);
    });

    // 'element.hover',
    // 'element.out',
    // 'element.click',
    // 'element.dblclick',
    // 'element.mousedown',
    // 'element.mouseup',
    diagramModeler.on('element.click', (element: any) => {
      handleElementClick(element);
    });

    diagramModeler.on('spiff.service_tasks.requested', (event: any) => {
      handleServiceTasksRequested(event);
    });
  }, [
    diagramModelerState,
    diagramType,
    onLaunchScriptEditor,
    onElementClick,
    onServiceTasksRequested,
  ]);

  useEffect(() => {
    // These seem to be system tasks that cannot be highlighted
    const taskSpecsThatCannotBeHighlighted = ['Root', 'Start', 'End'];

    if (!diagramModelerState) {
      return undefined;
    }
    if (performingXmlUpdates) {
      return undefined;
    }

    function handleError(err: any) {
      console.log('ERROR:', err);
    }

    function checkTaskCanBeHighlighted(taskBpmnId: string) {
      return (
        !taskSpecsThatCannotBeHighlighted.includes(taskBpmnId) &&
        !taskBpmnId.match(/EndJoin/)
      );
    }

    function highlightBpmnIoElement(
      canvas: any,
      taskBpmnId: string,
      bpmnIoClassName: string
    ) {
      if (checkTaskCanBeHighlighted(taskBpmnId)) {
        try {
          canvas.addMarker(taskBpmnId, bpmnIoClassName);
        } catch (bpmnIoError: any) {
          // the task list also contains task for processes called from call activities which will
          // not exist in this diagram so just ignore them for now.
          if (
            bpmnIoError.message !==
            "Cannot read properties of undefined (reading 'id')"
          ) {
            throw bpmnIoError;
          }
        }
      }
    }

    function onImportDone(event: any) {
      const { error } = event;

      if (error) {
        handleError(error);
        return;
      }

      let modeler = diagramModelerState;
      if (diagramType === 'dmn') {
        modeler = (diagramModelerState as any).getActiveViewer();
      }

      const canvas = (modeler as any).get('canvas');

      // only get the canvas if the dmn active viewer is actually
      // a Modeler and not an Editor which is what it will when we are
      // actively editing a decision table
      if ((modeler as any).constructor.name === 'Modeler') {
        canvas.zoom('fit-viewport');
      }

      // highlighting a field
      // Option 3 at:
      //  https://github.com/bpmn-io/bpmn-js-examples/tree/master/colors
      if (readyOrWaitingBpmnTaskIds) {
        readyOrWaitingBpmnTaskIds.forEach((readyOrWaitingBpmnTaskId) => {
          highlightBpmnIoElement(
            canvas,
            readyOrWaitingBpmnTaskId,
            'active-task-highlight'
          );
        });
      }
      if (completedTasksBpmnIds) {
        completedTasksBpmnIds.forEach((completedTaskBpmnId) => {
          highlightBpmnIoElement(
            canvas,
            completedTaskBpmnId,
            'completed-task-highlight'
          );
        });
      }
    }

    function displayDiagram(
      diagramModelerToUse: any,
      diagramXMLToDisplay: any
    ) {
      if (alreadyImportedXmlRef.current) {
        return;
      }
      diagramModelerToUse.importXML(diagramXMLToDisplay);
      alreadyImportedXmlRef.current = true;
    }

    function fetchDiagramFromURL(urlToUse: any) {
      fetch(urlToUse)
        .then((response) => response.text())
        .then((text) => {
          const processId = `Proccess_${makeid(7)}`;
          const newText = text.replace('{{PROCESS_ID}}', processId);
          setDiagramXMLString(newText);
        })
        .catch((err) => handleError(err));
    }

    function setDiagramXMLStringFromResponseJson(result: any) {
      setDiagramXMLString(result.file_contents);
    }

    function fetchDiagramFromJsonAPI() {
      HttpService.makeCallToBackend({
        path: `/process-models/${processGroupId}/${processModelId}/files/${fileName}`,
        successCallback: setDiagramXMLStringFromResponseJson,
      });
    }

    (diagramModelerState as any).on('import.done', onImportDone);

    const diagramXMLToUse = diagramXML || diagramXMLString;
    if (diagramXMLToUse) {
      if (!diagramXMLString) {
        setDiagramXMLString(diagramXMLToUse);
      }
      displayDiagram(diagramModelerState, diagramXMLToUse);

      return undefined;
    }

    if (!diagramXMLString) {
      if (url) {
        fetchDiagramFromURL(url);
        return undefined;
      }
      if (fileName) {
        fetchDiagramFromJsonAPI();
        return undefined;
      }
      let newDiagramFileName = 'new_bpmn_diagram.bpmn';
      if (diagramType === 'dmn') {
        newDiagramFileName = 'new_dmn_diagram.dmn';
      }
      fetchDiagramFromURL(`${process.env.PUBLIC_URL}/${newDiagramFileName}`);
      return undefined;
    }

    return () => {
      (diagramModelerState as any).destroy();
    };
  }, [
    diagramModelerState,
    diagramType,
    diagramXML,
    diagramXMLString,
    readyOrWaitingBpmnTaskIds,
    completedTasksBpmnIds,
    fileName,
    performingXmlUpdates,
    processGroupId,
    processModelId,
    url,
  ]);

  function handleSave() {
    if (saveDiagram) {
      (diagramModelerState as any)
        .saveXML({ format: true })
        .then((xmlObject: any) => {
          saveDiagram(xmlObject.xml);
        });
    }
  }

  function handleDelete() {
    if (onDeleteFile) {
      onDeleteFile(fileName);
    }
  }

  function handleSetPrimaryFile() {
    if (onSetPrimaryFile) {
      onSetPrimaryFile(fileName);
    }
  }

  const downloadXmlFile = () => {
    (diagramModelerState as any)
      .saveXML({ format: true })
      .then((xmlObject: any) => {
        const element = document.createElement('a');
        const file = new Blob([xmlObject.xml], {
          type: 'application/xml',
        });
        let downloadFileName = fileName;
        if (!downloadFileName) {
          downloadFileName = `${processModelId}.${diagramType}`;
        }
        element.href = URL.createObjectURL(file);
        element.download = downloadFileName;
        document.body.appendChild(element);
        element.click();
      });
  };

  const userActionOptions = () => {
    if (diagramType !== 'readonly') {
      return (
        <>
          <Button onClick={handleSave} variant="danger">
            Save
          </Button>
          {fileName && (
            <ButtonWithConfirmation
              description={`Delete file ${fileName}?`}
              onConfirmation={handleDelete}
              buttonLabel="Delete"
            />
          )}
          {onSetPrimaryFile && (
            <Button onClick={handleSetPrimaryFile}>Set as primary file</Button>
          )}
          <Button onClick={downloadXmlFile}>Download xml</Button>
        </>
      );
    }
    return null;
  };

  return <div>{userActionOptions()}</div>;
}
