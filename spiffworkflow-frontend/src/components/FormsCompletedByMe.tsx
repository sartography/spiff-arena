// import { useEffect, useState } from 'react';
// import { Modal } from '@carbon/react';
// import { useSearchParams } from 'react-router-dom';
// import PaginationForTable from './PaginationForTable';
// import { getPageInfoFromSearchParams } from '../helpers';
// import HttpService from '../services/HttpService';
// import { MessageInstance } from '../interfaces';
// import TaskListTable from './TaskListTable';
//
// type OwnProps = {
//   processInstanceId?: number;
// };
//
// export default function FormsCompletedByMe({ processInstanceId }: OwnProps) {
//   const [messageIntances, setMessageInstances] = useState([]);
//   const [pagination, setPagination] = useState(null);
//   const [searchParams] = useSearchParams();
//
//   const [messageInstanceForModal, setMessageInstanceForModal] =
//     useState<MessageInstance | null>(null);
//
//   useEffect(() => {
//     const setMessageInstanceListFromResult = (result: any) => {
//       setMessageInstances(result.results);
//       setPagination(result.pagination);
//     };
//     const { page, perPage } = getPageInfoFromSearchParams(searchParams);
//     const queryParamString = `per_page=${perPage}&page=${page}`;
//
//     HttpService.makeCallToBackend({
//       path: `/tasks/completed-by-me/${processInstanceId}?${queryParamString}`,
//       successCallback: setMessageInstanceListFromResult,
//     });
//   }, [processInstanceId, searchParams]);
//
//   const handleCorrelationDisplayClose = () => {
//     setMessageInstanceForModal(null);
//   };
//
//   const correlationsDisplayModal = () => {
//     if (messageInstanceForModal) {
//       let failureCausePre = null;
//       if (messageInstanceForModal.failure_cause) {
//         failureCausePre = (
//           <>
//             <p className="failure-string">
//               {messageInstanceForModal.failure_cause}
//             </p>
//             <br />
//           </>
//         );
//       }
//       return (
//         <Modal
//           open={!!messageInstanceForModal}
//           passiveModal
//           onRequestClose={handleCorrelationDisplayClose}
//           modalHeading={`Message ${messageInstanceForModal.id} (${messageInstanceForModal.name}) ${messageInstanceForModal.message_type} data:`}
//           modalLabel="Details"
//         >
//           {failureCausePre}
//           <p>Correlations:</p>
//           <pre>
//             {JSON.stringify(messageInstanceForModal.correlation_keys, null, 2)}
//           </pre>
//         </Modal>
//       );
//     }
//     return null;
//   };
//
//   const buildTable = () => {
//     return (
//       <TaskListTable
//         apiPath="/tasks"
//         additionalParams={`process_instance_id=${processInstance.id}`}
//         tableTitle="Tasks I can complete"
//         tableDescription="These are tasks that can be completed by you, either because they were assigned to a group you are in, or because they were assigned directly to you."
//         paginationClassName="with-large-bottom-margin"
//         textToShowIfEmpty="There are no tasks you can complete for this process instance."
//         shouldPaginateTable={false}
//         showProcessModelIdentifier={false}
//         showProcessId={false}
//         showStartedBy={false}
//         showTableDescriptionAsTooltip
//         showDateStarted={false}
//         showLastUpdated={false}
//         hideIfNoTasks
//         canCompleteAllTasks
//       />
//     );
//   };
//
//   if (pagination) {
//     const { page, perPage } = getPageInfoFromSearchParams(searchParams);
//     return (
//       <PaginationForTable
//         page={page}
//         perPage={perPage}
//         pagination={pagination}
//         tableToDisplay={buildTable()}
//         paginationQueryParamPrefix="forms-completed-by-me"
//       />
//     );
//   }
//   return null;
// }
