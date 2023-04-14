// // @ts-ignore
// import { Filter } from '@carbon/icons-react';
// import {
//   Button,
//   Grid,
//   Column,
//   // @ts-ignore
// } from '@carbon/react';
// import useAPIError from '../hooks/UseApiError';
//
// type OwnProps = {
//   showFilterOptions: boolean;
//   setShowFilterOptions: Function;
//   filtersEnabled?: boolean;
// };
//
// export default function Filters({
//   showFilterOptions,
//   setShowFilterOptions,
//   filtersEnabled = true,
// }: OwnProps) {
//   const { addError, removeError } = useAPIError();
//
//   const toggleShowFilterOptions = () => {
//     setShowFilterOptions(!showFilterOptions);
//   };
//   const reportFilterBy = () => {
//     return (reportMetadata as any).filter_by;
//   };
//   const reportColumns = () => {
//     return (reportMetadata as any).columns;
//   };
//
//   const navigateToNewReport = (queryParamString: string) => {
//     removeError();
//     setProcessInstanceReportJustSaved(null);
//     setProcessInstanceFilters({});
//     navigate(`${processInstanceListPathPrefix}?${queryParamString}`);
//   };
//
//   const applyFilter = (event: any) => {
//     event.preventDefault();
//     setProcessInitiatorNotFoundErrorText('');
//
//     const { page, perPage } = getPageInfoFromSearchParams(
//       searchParams,
//       undefined,
//       undefined,
//       paginationQueryParamPrefix
//     );
//     let queryParamString = `per_page=${perPage}&page=${page}&user_filter=true`;
//     const {
//       valid,
//       startFromSeconds,
//       startToSeconds,
//       endFromSeconds,
//       endToSeconds,
//     } = calculateStartAndEndSeconds();
//
//     if (!valid) {
//       return;
//     }
//
//     if (startFromSeconds) {
//       queryParamString += `&start_from=${startFromSeconds}`;
//     }
//     if (startToSeconds) {
//       queryParamString += `&start_to=${startToSeconds}`;
//     }
//     if (endFromSeconds) {
//       queryParamString += `&end_from=${endFromSeconds}`;
//     }
//     if (endToSeconds) {
//       queryParamString += `&end_to=${endToSeconds}`;
//     }
//     if (processStatusSelection.length > 0) {
//       queryParamString += `&process_status=${processStatusSelection}`;
//     }
//
//     if (processModelSelection) {
//       queryParamString += `&process_model_identifier=${processModelSelection.id}`;
//     }
//
//     if (processInstanceReportSelection) {
//       queryParamString += `&report_id=${processInstanceReportSelection.id}`;
//     }
//
//     const reportColumnsBase64 = encodeBase64(JSON.stringify(reportColumns()));
//     queryParamString += `&report_columns=${reportColumnsBase64}`;
//     const reportFilterByBase64 = encodeBase64(JSON.stringify(reportFilterBy()));
//     queryParamString += `&report_filter_by=${reportFilterByBase64}`;
//
//     if (processInitiatorSelection) {
//       queryParamString += `&process_initiator_username=${processInitiatorSelection.username}`;
//       navigateToNewReport(queryParamString);
//     } else if (processInitiatorText) {
//       HttpService.makeCallToBackend({
//         path: targetUris.userExists,
//         httpMethod: 'POST',
//         postBody: { username: processInitiatorText },
//         successCallback: (result: any) => {
//           if (result.user_found) {
//             queryParamString += `&process_initiator_username=${processInitiatorText}`;
//             navigateToNewReport(queryParamString);
//           } else {
//             setProcessInitiatorNotFoundErrorText(
//               `The provided username is invalid. Please type the exact username.`
//             );
//           }
//         },
//       });
//     } else {
//       navigateToNewReport(queryParamString);
//     }
//   };
//
//   const dateComponent = (
//     labelString: any,
//     name: any,
//     initialDate: any,
//     initialTime: string,
//     onChangeDateFunction: any,
//     onChangeTimeFunction: any,
//     timeInvalid: boolean,
//     setTimeInvalid: any
//   ) => {
//     return (
//       <>
//         <DatePicker dateFormat={DATE_FORMAT_CARBON} datePickerType="single">
//           <DatePickerInput
//             id={`date-picker-${name}`}
//             placeholder={DATE_FORMAT}
//             labelText={labelString}
//             type="text"
//             size="md"
//             autocomplete="off"
//             allowInput={false}
//             onChange={(dateChangeEvent: any) => {
//               if (!initialDate && !initialTime) {
//                 onChangeTimeFunction(
//                   convertDateObjectToFormattedHoursMinutes(new Date())
//                 );
//               }
//               onChangeDateFunction(dateChangeEvent.srcElement.value);
//             }}
//             value={initialDate}
//           />
//         </DatePicker>
//         <TimePicker
//           invalid={timeInvalid}
//           id="time-picker"
//           labelText="Select a time"
//           pattern="^([01]\d|2[0-3]):?([0-5]\d)$"
//           value={initialTime}
//           onChange={(event: any) => {
//             if (event.srcElement.validity.valid) {
//               setTimeInvalid(false);
//             } else {
//               setTimeInvalid(true);
//             }
//             onChangeTimeFunction(event.srcElement.value);
//           }}
//         />
//       </>
//     );
//   };
//
//   const processStatusSearch = () => {
//     return (
//       <MultiSelect
//         label="Choose Status"
//         className="our-class"
//         id="process-instance-status-select"
//         titleText="Status"
//         items={processStatusAllOptions}
//         onChange={(selection: any) => {
//           setProcessStatusSelection(selection.selectedItems);
//           setRequiresRefilter(true);
//         }}
//         itemToString={(item: any) => {
//           return item || '';
//         }}
//         selectionFeedback="top-after-reopen"
//         selectedItems={processStatusSelection}
//       />
//     );
//   };
//
//   const clearFilters = () => {
//     setProcessModelSelection(null);
//     setProcessStatusSelection([]);
//     setStartFromDate('');
//     setStartFromTime('');
//     setStartToDate('');
//     setStartToTime('');
//     setEndFromDate('');
//     setEndFromTime('');
//     setEndToDate('');
//     setEndToTime('');
//     setProcessInitiatorSelection(null);
//     setProcessInitiatorText('');
//     setRequiresRefilter(true);
//     if (reportMetadata) {
//       reportMetadata.filter_by = [];
//     }
//   };
//
//   const processInstanceReportDidChange = (selection: any, mode?: string) => {
//     clearFilters();
//     const selectedReport = selection.selectedItem;
//     setProcessInstanceReportSelection(selectedReport);
//
//     let queryParamString = '';
//     if (selectedReport) {
//       queryParamString = `?report_id=${selectedReport.id}`;
//     }
//
//     removeError();
//     setProcessInstanceReportJustSaved(mode || null);
//     navigate(`${processInstanceListPathPrefix}${queryParamString}`);
//   };
//
//   const reportColumnAccessors = () => {
//     return reportColumns().map((reportColumn: ReportColumn) => {
//       return reportColumn.accessor;
//     });
//   };
//
//   // TODO onSuccess reload/select the new report in the report search
//   const onSaveReportSuccess = (result: any, mode: string) => {
//     processInstanceReportDidChange(
//       {
//         selectedItem: result,
//       },
//       mode
//     );
//   };
//
//   const saveAsReportComponent = () => {
//     const {
//       valid,
//       startFromSeconds,
//       startToSeconds,
//       endFromSeconds,
//       endToSeconds,
//     } = calculateStartAndEndSeconds(false);
//
//     if (!valid || !reportMetadata) {
//       return null;
//     }
//     return (
//       <ProcessInstanceListSaveAsReport
//         onSuccess={onSaveReportSuccess}
//         buttonClassName="button-white-background narrow-button"
//         columnArray={reportColumns()}
//         orderBy=""
//         buttonText="Save"
//         processModelSelection={processModelSelection}
//         processInitiatorSelection={processInitiatorSelection}
//         processStatusSelection={processStatusSelection}
//         processInstanceReportSelection={processInstanceReportSelection}
//         reportMetadata={reportMetadata}
//         startFromSeconds={startFromSeconds}
//         startToSeconds={startToSeconds}
//         endFromSeconds={endFromSeconds}
//         endToSeconds={endToSeconds}
//       />
//     );
//   };
//
//   const onDeleteReportSuccess = () => {
//     processInstanceReportDidChange({ selectedItem: null });
//   };
//
//   const deleteReportComponent = () => {
//     return processInstanceReportSelection ? (
//       <ProcessInstanceListDeleteReport
//         onSuccess={onDeleteReportSuccess}
//         processInstanceReportSelection={processInstanceReportSelection}
//       />
//     ) : null;
//   };
//
//   const removeColumn = (reportColumn: ReportColumn) => {
//     if (reportMetadata) {
//       const reportMetadataCopy = { ...reportMetadata };
//       const newColumns = reportColumns().filter(
//         (rc: ReportColumn) => rc.accessor !== reportColumn.accessor
//       );
//       Object.assign(reportMetadataCopy, { columns: newColumns });
//       setReportMetadata(reportMetadataCopy);
//       setRequiresRefilter(true);
//     }
//   };
//
//   const handleColumnFormClose = () => {
//     setShowReportColumnForm(false);
//     setReportColumnFormMode('');
//     setReportColumnToOperateOn(null);
//   };
//
//   const getFilterByFromReportMetadata = (reportColumnAccessor: string) => {
//     if (reportMetadata) {
//       return reportMetadata.filter_by.find((reportFilter: ReportFilter) => {
//         return reportColumnAccessor === reportFilter.field_name;
//       });
//     }
//     return null;
//   };
//
//   const getNewFiltersFromReportForEditing = (
//     reportColumnForEditing: ReportColumnForEditing
//   ) => {
//     if (!reportMetadata) {
//       return null;
//     }
//     const reportMetadataCopy = { ...reportMetadata };
//     let newReportFilters = reportMetadataCopy.filter_by;
//     if (reportColumnForEditing.filterable) {
//       const newReportFilter: ReportFilter = {
//         field_name: reportColumnForEditing.accessor,
//         field_value: reportColumnForEditing.filter_field_value,
//         operator: reportColumnForEditing.filter_operator || 'equals',
//       };
//       const existingReportFilter = getFilterByFromReportMetadata(
//         reportColumnForEditing.accessor
//       );
//       if (existingReportFilter) {
//         const existingReportFilterIndex =
//           reportMetadataCopy.filter_by.indexOf(existingReportFilter);
//         if (reportColumnForEditing.filter_field_value) {
//           newReportFilters[existingReportFilterIndex] = newReportFilter;
//         } else {
//           newReportFilters.splice(existingReportFilterIndex, 1);
//         }
//       } else if (reportColumnForEditing.filter_field_value) {
//         newReportFilters = newReportFilters.concat([newReportFilter]);
//       }
//     }
//     return newReportFilters;
//   };
//
//   const handleUpdateReportColumn = () => {
//     if (reportColumnToOperateOn && reportMetadata) {
//       const reportMetadataCopy = { ...reportMetadata };
//       let newReportColumns = null;
//       if (reportColumnFormMode === 'new') {
//         newReportColumns = reportColumns().concat([reportColumnToOperateOn]);
//       } else {
//         newReportColumns = reportColumns().map((rc: ReportColumn) => {
//           if (rc.accessor === reportColumnToOperateOn.accessor) {
//             return reportColumnToOperateOn;
//           }
//           return rc;
//         });
//       }
//       Object.assign(reportMetadataCopy, {
//         columns: newReportColumns,
//         filter_by: getNewFiltersFromReportForEditing(reportColumnToOperateOn),
//       });
//       setReportMetadata(reportMetadataCopy);
//       setReportColumnToOperateOn(null);
//       setShowReportColumnForm(false);
//       setRequiresRefilter(true);
//     }
//   };
//
//   const reportColumnToReportColumnForEditing = (reportColumn: ReportColumn) => {
//     const reportColumnForEditing: ReportColumnForEditing = Object.assign(
//       reportColumn,
//       { filter_field_value: '', filter_operator: '' }
//     );
//     const reportFilter = getFilterByFromReportMetadata(
//       reportColumnForEditing.accessor
//     );
//     if (reportFilter) {
//       reportColumnForEditing.filter_field_value = reportFilter.field_value;
//       reportColumnForEditing.filter_operator =
//         reportFilter.operator || 'equals';
//     }
//     return reportColumnForEditing;
//   };
//
//   const updateReportColumn = (event: any) => {
//     let reportColumnForEditing = null;
//     if (event.selectedItem) {
//       reportColumnForEditing = reportColumnToReportColumnForEditing(
//         event.selectedItem
//       );
//     }
//     setReportColumnToOperateOn(reportColumnForEditing);
//     setRequiresRefilter(true);
//   };
//
//   // options includes item and inputValue
//   const shouldFilterReportColumn = (options: any) => {
//     const reportColumn: ReportColumn = options.item;
//     const { inputValue } = options;
//     return (
//       !reportColumnAccessors().includes(reportColumn.accessor) &&
//       (reportColumn.accessor || '')
//         .toLowerCase()
//         .includes((inputValue || '').toLowerCase())
//     );
//   };
//
//   const setReportColumnConditionValue = (event: any) => {
//     if (reportColumnToOperateOn) {
//       const reportColumnToOperateOnCopy = {
//         ...reportColumnToOperateOn,
//       };
//       reportColumnToOperateOnCopy.filter_field_value = event.target.value;
//       setReportColumnToOperateOn(reportColumnToOperateOnCopy);
//       setRequiresRefilter(true);
//     }
//   };
//
//   const reportColumnForm = () => {
//     if (reportColumnFormMode === '') {
//       return null;
//     }
//     const formElements = [];
//     if (reportColumnFormMode === 'new') {
//       formElements.push(
//         <ComboBox
//           onChange={updateReportColumn}
//           id="report-column-selection"
//           data-qa="report-column-selection"
//           data-modal-primary-focus
//           items={availableReportColumns}
//           itemToString={(reportColumn: ReportColumn) => {
//             if (reportColumn) {
//               return reportColumn.accessor;
//             }
//             return null;
//           }}
//           shouldFilterItem={shouldFilterReportColumn}
//           placeholder="Choose a column to show"
//           titleText="Column"
//           selectedItem={reportColumnToOperateOn}
//         />
//       );
//     }
//     formElements.push([
//       <TextInput
//         id="report-column-display-name"
//         name="report-column-display-name"
//         labelText="Display Name"
//         disabled={!reportColumnToOperateOn}
//         value={reportColumnToOperateOn ? reportColumnToOperateOn.Header : ''}
//         onChange={(event: any) => {
//           if (reportColumnToOperateOn) {
//             setRequiresRefilter(true);
//             const reportColumnToOperateOnCopy = {
//               ...reportColumnToOperateOn,
//             };
//             reportColumnToOperateOnCopy.Header = event.target.value;
//             setReportColumnToOperateOn(reportColumnToOperateOnCopy);
//           }
//         }}
//       />,
//     ]);
//     if (reportColumnToOperateOn && reportColumnToOperateOn.filterable) {
//       formElements.push(
//         <TextInput
//           id="report-column-condition-value"
//           name="report-column-condition-value"
//           labelText="Condition Value"
//           value={
//             reportColumnToOperateOn
//               ? reportColumnToOperateOn.filter_field_value
//               : ''
//           }
//           onChange={setReportColumnConditionValue}
//         />
//       );
//     }
//     formElements.push(
//       <div className="vertical-spacer-to-allow-combo-box-to-expand-in-modal" />
//     );
//     const modalHeading =
//       reportColumnFormMode === 'new'
//         ? 'Add Column'
//         : `Edit ${
//             reportColumnToOperateOn ? reportColumnToOperateOn.accessor : ''
//           } column`;
//     return (
//       <Modal
//         open={showReportColumnForm}
//         modalHeading={modalHeading}
//         primaryButtonText="Save"
//         primaryButtonDisabled={!reportColumnToOperateOn}
//         onRequestSubmit={handleUpdateReportColumn}
//         onRequestClose={handleColumnFormClose}
//         hasScrollingContent
//       >
//         {formElements}
//       </Modal>
//     );
//   };
//
//   const columnSelections = () => {
//     if (reportColumns()) {
//       const tags: any = [];
//
//       (reportColumns() as any).forEach((reportColumn: ReportColumn) => {
//         const reportColumnForEditing =
//           reportColumnToReportColumnForEditing(reportColumn);
//
//         let tagType = 'cool-gray';
//         let tagTypeClass = '';
//         if (reportColumnForEditing.filterable) {
//           tagType = 'green';
//           tagTypeClass = 'tag-type-green';
//         }
//         let reportColumnLabel = reportColumnForEditing.Header;
//         if (reportColumnForEditing.filter_field_value) {
//           reportColumnLabel = `${reportColumnLabel}=${reportColumnForEditing.filter_field_value}`;
//         }
//         tags.push(
//           <Tag type={tagType} size="sm">
//             <Button
//               kind="ghost"
//               size="sm"
//               className={`button-tag-icon ${tagTypeClass}`}
//               title={`Edit ${reportColumnForEditing.accessor} column`}
//               onClick={() => {
//                 setReportColumnToOperateOn(reportColumnForEditing);
//                 setShowReportColumnForm(true);
//                 setReportColumnFormMode('edit');
//               }}
//             >
//               {reportColumnLabel}
//             </Button>
//             <Button
//               data-qa="remove-report-column"
//               renderIcon={Close}
//               iconDescription="Remove Column"
//               className={`button-tag-icon ${tagTypeClass}`}
//               hasIconOnly
//               size="sm"
//               kind="ghost"
//               onClick={() => removeColumn(reportColumnForEditing)}
//             />
//           </Tag>
//         );
//       });
//       return (
//         <Stack orientation="horizontal">
//           {tags}
//           <Button
//             data-qa="add-column-button"
//             renderIcon={AddAlt}
//             iconDescription="Column options"
//             className="with-tiny-top-margin"
//             kind="ghost"
//             hasIconOnly
//             size="sm"
//             onClick={() => {
//               setShowReportColumnForm(true);
//               setReportColumnFormMode('new');
//             }}
//           />
//         </Stack>
//       );
//     }
//     return null;
//   };
//
//   const filterOptions = () => {
//     if (!showFilterOptions) {
//       return null;
//     }
//
//     let queryParamString = '';
//     if (processModelSelection) {
//       queryParamString += `?process_model_identifier=${processModelSelection.id}`;
//     }
//     // get the columns anytime we display the filter options if they are empty.
//     // and if the columns are not empty, check if the columns are stale
//     // because we selected a different process model in the filter options.
//     const columnFilterIsStale = lastColumnFilter !== queryParamString;
//     if (availableReportColumns.length < 1 || columnFilterIsStale) {
//       setLastColumnFilter(queryParamString);
//       HttpService.makeCallToBackend({
//         path: `/process-instances/reports/columns${queryParamString}`,
//         successCallback: setAvailableReportColumns,
//       });
//     }
//
//     return (
//       <>
//         <Grid fullWidth className="with-bottom-margin">
//           <Column md={8} lg={16} sm={4}>
//             <FormLabel>Columns</FormLabel>
//             <br />
//             {columnSelections()}
//           </Column>
//         </Grid>
//         <Grid fullWidth className="with-bottom-margin">
//           <Column md={8}>
//             <ProcessModelSearch
//               onChange={(selection: any) => {
//                 setProcessModelSelection(selection.selectedItem);
//                 setRequiresRefilter(true);
//               }}
//               processModels={processModelAvailableItems}
//               selectedItem={processModelSelection}
//             />
//           </Column>
//           <Column md={4}>
//             <Can
//               I="GET"
//               a={targetUris.userSearch}
//               ability={ability}
//               passThrough
//             >
//               {(hasAccess: boolean) => {
//                 if (hasAccess) {
//                   return (
//                     <ComboBox
//                       onInputChange={searchForProcessInitiator}
//                       onChange={(event: any) => {
//                         setProcessInitiatorSelection(event.selectedItem);
//                         setRequiresRefilter(true);
//                       }}
//                       id="process-instance-initiator-search"
//                       data-qa="process-instance-initiator-search"
//                       items={processInstanceInitiatorOptions}
//                       itemToString={(processInstanceInitatorOption: User) => {
//                         if (processInstanceInitatorOption) {
//                           return processInstanceInitatorOption.username;
//                         }
//                         return null;
//                       }}
//                       placeholder="Start typing username"
//                       titleText="Process Initiator"
//                       selectedItem={processInitiatorSelection}
//                     />
//                   );
//                 }
//                 return (
//                   <TextInput
//                     id="process-instance-initiator-search"
//                     placeholder="Enter username"
//                     labelText="Process Initiator"
//                     invalid={processInitiatorNotFoundErrorText !== ''}
//                     invalidText={processInitiatorNotFoundErrorText}
//                     onChange={(event: any) => {
//                       setProcessInitiatorText(event.target.value);
//                       setRequiresRefilter(true);
//                     }}
//                   />
//                 );
//               }}
//             </Can>
//           </Column>
//           <Column md={4}>{processStatusSearch()}</Column>
//         </Grid>
//         <Grid fullWidth className="with-bottom-margin">
//           <Column md={4}>
//             {dateComponent(
//               'Start date from',
//               'start-from',
//               startFromDate,
//               startFromTime,
//               (val: string) => {
//                 setStartFromDate(val);
//                 setRequiresRefilter(true);
//               },
//               (val: string) => {
//                 setStartFromTime(val);
//                 setRequiresRefilter(true);
//               },
//               startFromTimeInvalid,
//               setStartFromTimeInvalid
//             )}
//           </Column>
//           <Column md={4}>
//             {dateComponent(
//               'Start date to',
//               'start-to',
//               startToDate,
//               startToTime,
//               (val: string) => {
//                 setStartToDate(val);
//                 setRequiresRefilter(true);
//               },
//               (val: string) => {
//                 setStartToTime(val);
//                 setRequiresRefilter(true);
//               },
//               startToTimeInvalid,
//               setStartToTimeInvalid
//             )}
//           </Column>
//           <Column md={4}>
//             {dateComponent(
//               'End date from',
//               'end-from',
//               endFromDate,
//               endFromTime,
//               (val: string) => {
//                 setEndFromDate(val);
//                 setRequiresRefilter(true);
//               },
//               (val: string) => {
//                 setEndFromTime(val);
//                 setRequiresRefilter(true);
//               },
//               endFromTimeInvalid,
//               setEndFromTimeInvalid
//             )}
//           </Column>
//           <Column md={4}>
//             {dateComponent(
//               'End date to',
//               'end-to',
//               endToDate,
//               endToTime,
//               (val: string) => {
//                 setEndToDate(val);
//                 setRequiresRefilter(true);
//               },
//               (val: string) => {
//                 setEndToTime(val);
//                 setRequiresRefilter(true);
//               },
//               endToTimeInvalid,
//               setEndToTimeInvalid
//             )}
//           </Column>
//         </Grid>
//         <Grid fullWidth className="with-bottom-margin">
//           <Column sm={4} md={4} lg={8}>
//             <ButtonSet>
//               <Button
//                 kind=""
//                 className="button-white-background narrow-button"
//                 onClick={clearFilters}
//               >
//                 Clear
//               </Button>
//               <Button
//                 kind="secondary"
//                 disabled={!requiresRefilter}
//                 onClick={applyFilter}
//                 data-qa="filter-button"
//                 className="narrow-button"
//               >
//                 Apply
//               </Button>
//             </ButtonSet>
//           </Column>
//           <Column sm={4} md={4} lg={8}>
//             {saveAsReportComponent()}
//             {deleteReportComponent()}
//           </Column>
//         </Grid>
//       </>
//     );
//   };
//
//   const getWaitingForTableCellComponent = (processInstanceTask: any) => {
//     let fullUsernameString = '';
//     let shortUsernameString = '';
//     if (processInstanceTask.potential_owner_usernames) {
//       fullUsernameString = processInstanceTask.potential_owner_usernames;
//       const usernames =
//         processInstanceTask.potential_owner_usernames.split(',');
//       const firstTwoUsernames = usernames.slice(0, 2);
//       if (usernames.length > 2) {
//         firstTwoUsernames.push('...');
//       }
//       shortUsernameString = firstTwoUsernames.join(',');
//     }
//     if (processInstanceTask.assigned_user_group_identifier) {
//       fullUsernameString = processInstanceTask.assigned_user_group_identifier;
//       shortUsernameString = processInstanceTask.assigned_user_group_identifier;
//     }
//     return <span title={fullUsernameString}>{shortUsernameString}</span>;
//   };
//   const formatProcessInstanceId = (row: ProcessInstance, id: number) => {
//     return <span data-qa="paginated-entity-id">{id}</span>;
//   };
//   const formatProcessModelIdentifier = (_row: any, identifier: any) => {
//     return <span>{identifier}</span>;
//   };
//   const formatProcessModelDisplayName = (_row: any, identifier: any) => {
//     return <span>{identifier}</span>;
//   };
//
//   const formatSecondsForDisplay = (_row: any, seconds: any) => {
//     return convertSecondsToFormattedDateTime(seconds) || '-';
//   };
//   const defaultFormatter = (_row: any, value: any) => {
//     return value;
//   };
//
//   const formattedColumn = (row: any, column: any) => {
//     const reportColumnFormatters: Record<string, any> = {
//       id: formatProcessInstanceId,
//       process_model_identifier: formatProcessModelIdentifier,
//       process_model_display_name: formatProcessModelDisplayName,
//       start_in_seconds: formatSecondsForDisplay,
//       end_in_seconds: formatSecondsForDisplay,
//       updated_at_in_seconds: formatSecondsForDisplay,
//     };
//     const formatter =
//       reportColumnFormatters[column.accessor] ?? defaultFormatter;
//     const value = row[column.accessor];
//     const modifiedModelId = modifyProcessIdentifierForPathParam(
//       row.process_model_identifier
//     );
//     const navigateToProcessInstance = () => {
//       navigate(`${processInstanceShowPathPrefix}/${modifiedModelId}/${row.id}`);
//     };
//     const navigateToProcessModel = () => {
//       navigate(`/admin/process-models/${modifiedModelId}`);
//     };
//
//     if (column.accessor === 'status') {
//       return (
//         // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
//         <td
//           onClick={navigateToProcessInstance}
//           onKeyDown={navigateToProcessInstance}
//           data-qa={`process-instance-status-${value}`}
//         >
//           {formatter(row, value)}
//         </td>
//       );
//     }
//     if (column.accessor === 'process_model_display_name') {
//       const pmStyle = { background: 'rgba(0, 0, 0, .02)' };
//       return (
//         // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
//         <td
//           style={pmStyle}
//           onClick={navigateToProcessModel}
//           onKeyDown={navigateToProcessModel}
//         >
//           {formatter(row, value)}
//         </td>
//       );
//     }
//     if (column.accessor === 'waiting_for') {
//       return <td>{getWaitingForTableCellComponent(row)}</td>;
//     }
//     if (column.accessor === 'updated_at_in_seconds') {
//       return (
//         <TableCellWithTimeAgoInWords
//           timeInSeconds={row.updated_at_in_seconds}
//         />
//       );
//     }
//     return (
//       // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
//       <td
//         data-qa={`process-instance-show-link-${column.accessor}`}
//         onKeyDown={navigateToProcessModel}
//         onClick={navigateToProcessInstance}
//       >
//         {formatter(row, value)}
//       </td>
//     );
//   };
//
//   const buildTable = () => {
//     const headerLabels: Record<string, string> = {
//       id: 'Id',
//       process_model_identifier: 'Process',
//       process_model_display_name: 'Process',
//       start_in_seconds: 'Start Time',
//       end_in_seconds: 'End Time',
//       status: 'Status',
//       process_initiator_username: 'Started By',
//     };
//     const getHeaderLabel = (header: string) => {
//       return headerLabels[header] ?? header;
//     };
//     const headers = reportColumns().map((column: any) => {
//       return getHeaderLabel((column as any).Header);
//     });
//     if (showActionsColumn) {
//       headers.push('Actions');
//     }
//
//     const rows = processInstances.map((row: any) => {
//       const currentRow = reportColumns().map((column: any) => {
//         return formattedColumn(row, column);
//       });
//       if (showActionsColumn) {
//         let buttonElement = null;
//         if (row.task_id) {
//           const taskUrl = `/tasks/${row.id}/${row.task_id}`;
//           const regex = new RegExp(`\\b(${preferredUsername}|${userEmail})\\b`);
//           let hasAccessToCompleteTask = false;
//           if (
//             canCompleteAllTasks ||
//             (row.potential_owner_usernames || '').match(regex)
//           ) {
//             hasAccessToCompleteTask = true;
//           }
//           buttonElement = (
//             <Button
//               variant="primary"
//               href={taskUrl}
//               hidden={row.status === 'suspended'}
//               disabled={!hasAccessToCompleteTask}
//             >
//               Go
//             </Button>
//           );
//         }
//
//         currentRow.push(<td>{buttonElement}</td>);
//       }
//
//       const rowStyle = { cursor: 'pointer' };
//
//       return (
//         <tr style={rowStyle} key={row.id}>
//           {currentRow}
//         </tr>
//       );
//     });
//
//     return (
//       <Table size="lg">
//         <TableHead>
//           <TableRow>
//             {headers.map((header: any) => (
//               <TableHeader
//                 key={header}
//                 title={header === 'Id' ? 'Process Instance Id' : null}
//               >
//                 {header}
//               </TableHeader>
//             ))}
//           </TableRow>
//         </TableHead>
//         <tbody>{rows}</tbody>
//       </Table>
//     );
//   };
//
//   const reportSearchComponent = () => {
//     if (showReports) {
//       const columns = [
//         <Column sm={2} md={4} lg={7}>
//           <ProcessInstanceReportSearch
//             onChange={processInstanceReportDidChange}
//             selectedItem={processInstanceReportSelection}
//           />
//         </Column>,
//       ];
//       return (
//         <Grid className="with-tiny-bottom-margin" fullWidth>
//           {columns}
//         </Grid>
//       );
//     }
//     return null;
//   };
//
//   if (filtersEnabled) {
//     return (
//       <>
//         <Grid fullWidth>
//           <Column sm={2} md={4} lg={7}>
//             {reportSearchComponent()}
//           </Column>
//           <Column
//             className="filterIcon"
//             sm={{ span: 1, offset: 3 }}
//             md={{ span: 1, offset: 7 }}
//             lg={{ span: 1, offset: 15 }}
//           >
//             <Button
//               data-qa="filter-section-expand-toggle"
//               renderIcon={Filter}
//               iconDescription="Filter Options"
//               hasIconOnly
//               size="lg"
//               onClick={toggleShowFilterOptions}
//             />
//           </Column>
//         </Grid>
//         {filterOptions()}
//       </>
//     );
//   }
//   return null;
// }
