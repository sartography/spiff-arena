import { useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { Tabs, TabList, Tab } from '@carbon/react';
import TaskShow from './TaskShow';
import MyTasks from './MyTasks';
import CompletedInstances from './CompletedInstances';
import CreateNewInstance from './CreateNewInstance';
import InProgressInstances from './InProgressInstances';
import OnboardingView from './OnboardingView';
import ErrorDisplay from '../components/ErrorDisplay';
import ProcessGroupList from './ProcessGroupList';
import ProcessGroupShow from './ProcessGroupShow';
import ProcessGroupNew from './ProcessGroupNew';
import ProcessGroupEdit from './ProcessGroupEdit';
import ProcessModelShow from './ProcessModelShow';
import ProcessInstanceList from './ProcessInstanceList';
import ProcessModelNew from './ProcessModelNew';
import ProcessModelEdit from './ProcessModelEdit';
import ProcessInstanceShow from './ProcessInstanceShow';
import ProcessInstanceReportList from './ProcessInstanceReportList';
import ProcessInstanceReportNew from './ProcessInstanceReportNew';
import ProcessInstanceReportEdit from './ProcessInstanceReportEdit';
import ReactFormEditor from './ReactFormEditor';
import Configuration from './Configuration';
import JsonSchemaFormBuilder from './JsonSchemaFormBuilder';
import ProcessModelNewExperimental from './ProcessModelNewExperimental';
import ProcessInstanceFindById from './ProcessInstanceFindById';
import ProcessInterstitialPage from './ProcessInterstitialPage';
import MessageListPage from './MessageListPage';
import DataStorePage from './DataStorePage';
import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';

type OwnProps = {
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export default function HomePageRoutes({ extensionUxElements }: OwnProps) {
  const location = useLocation();
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const navigate = useNavigate();

  useEffect(() => {
    // Do not remove errors here, or they always get removed.
    let newSelectedTabIndex = 0;
    if (location.pathname.match(/^\/tasks\/completed-instances\b/)) {
      newSelectedTabIndex = 1;
    } else if (location.pathname.match(/^\/tasks\/create-new-instance\b/)) {
      newSelectedTabIndex = 2;
    }
    setSelectedTabIndex(newSelectedTabIndex);
  }, [location]);

  const renderTabs = () => {
    if (location.pathname.match(/^\/tasks\/\d+\/\b/)) {
      return null;
    }
    return (
      <>
        <Tabs selectedIndex={selectedTabIndex}>
          <TabList aria-label="List of tabs">
            {/* <Tab onClick={() => navigate('/tasks/my-tasks')}>My Tasks</Tab> */}
            <Tab onClick={() => navigate('/tasks/grouped')}>In Progress</Tab>
            <Tab onClick={() => navigate('/tasks/completed-instances')}>
              Completed
            </Tab>
            <Tab onClick={() => navigate('/tasks/create-new-instance')}>
              Start New +
            </Tab>
          </TabList>
        </Tabs>
        <br />
      </>
    );
  };

  return (
    <div className="fixed-width-container">
      <ErrorDisplay />
      <OnboardingView />
      {renderTabs()}
      <Routes>
        <Route path="/" element={<InProgressInstances />} />
        <Route path="my-tasks" element={<MyTasks />} />
        <Route path=":process_instance_id/:task_id" element={<TaskShow />} />
        <Route path="grouped" element={<InProgressInstances />} />
        <Route path="completed-instances" element={<CompletedInstances />} />
        <Route path="create-new-instance" element={<CreateNewInstance />} />
        <Route path="/" element={<ProcessGroupList />} />
        <Route path="process-groups" element={<ProcessGroupList />} />
        <Route
          path="process-groups/:process_group_id"
          element={<ProcessGroupShow />}
        />
        <Route path="process-groups/new" element={<ProcessGroupNew />} />
        <Route
          path="process-groups/:process_group_id/edit"
          element={<ProcessGroupEdit />}
        />

        <Route
          path="process-models/:process_group_id/new"
          element={<ProcessModelNew />}
        />
        <Route
          path="process-models/:process_group_id/new-e"
          element={<ProcessModelNewExperimental />}
        />
        <Route
          path="process-models/:process_model_id"
          element={<ProcessModelShow />}
        />
        <Route
          path="process-models/:process_model_id/edit"
          element={<ProcessModelEdit />}
        />
        <Route
          path="process-instances/for-me/:process_model_id/:process_instance_id"
          element={<ProcessInstanceShow variant="for-me" />}
        />
        <Route
          path="process-instances/for-me/:process_model_id/:process_instance_id/:to_task_guid"
          element={<ProcessInstanceShow variant="for-me" />}
        />
        <Route
          path="process-instances/for-me/:process_model_id/:process_instance_id/interstitial"
          element={<ProcessInterstitialPage variant="for-me" />}
        />
        <Route
          path="process-instances/:process_model_id/:process_instance_id/interstitial"
          element={<ProcessInterstitialPage variant="all" />}
        />
        <Route
          path="process-instances/:process_model_id/:process_instance_id"
          element={<ProcessInstanceShow variant="all" />}
        />
        <Route
          path="process-instances/:process_model_id/:process_instance_id/:to_task_guid"
          element={<ProcessInstanceShow variant="all" />}
        />
        <Route
          path="process-instances/reports"
          element={<ProcessInstanceReportList />}
        />
        <Route
          path="process-instances/reports/new"
          element={<ProcessInstanceReportNew />}
        />
        <Route
          path="process-instances/reports/:report_identifier/edit"
          element={<ProcessInstanceReportEdit />}
        />
        <Route
          path="process-models/:process_model_id/form"
          element={<ReactFormEditor />}
        />
        <Route
          path="process-models/:process_model_id/form/:file_name"
          element={<ReactFormEditor />}
        />
        <Route
          path="process-instances"
          element={<ProcessInstanceList variant="for-me" />}
        />
        <Route
          path="process-instances/for-me"
          element={<ProcessInstanceList variant="for-me" />}
        />
        <Route
          path="process-instances/all"
          element={<ProcessInstanceList variant="all" />}
        />
        <Route
          path="configuration/*"
          element={<Configuration extensionUxElements={extensionUxElements} />}
        />
        <Route
          path="process-models/:process_model_id/form-builder"
          element={<JsonSchemaFormBuilder />}
        />
        <Route
          path="process-instances/find-by-id"
          element={<ProcessInstanceFindById />}
        />
        <Route path="messages" element={<MessageListPage />} />
        <Route path="data-stores" element={<DataStorePage />} />
      </Routes>
    </div>
  );
}
