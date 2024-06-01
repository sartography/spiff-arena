import { Paper } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';

export default function TreePanel({
  processGroups,
}: {
  processGroups: Record<string, any>;
}) {
  const buildTree = (groups: Record<string, any>[]) => {
    return groups.map((group: Record<string, any>) => (
      <TreeItem key={group.id} itemId={group.id} label={group.display_name}>
        {group?.process_models?.map((pm: Record<string, any>) => (
          <TreeItem key={pm.id} itemId={pm.id} label={pm.display_name} />
        ))}
        {group?.process_groups?.length > 0 && buildTree(group.process_groups)}
      </TreeItem>
    ));
  };
  return (
    <Paper
      elevation={0}
      sx={{
        width: '100%',
        height: 'calc(100vh - 75px)',
        borderRadius: 0,
        borderRight: 1,
        borderRightColor: 'divider',
        borderRightStyle: 'solid',
        padding: 2,
        overflowY: 'auto',
      }}
    >
      <SimpleTreeView
        sx={{
          '& .MuiTreeItem-label': {
            fontSize: '12px !important',
            color: 'text.secondary',
          },
        }}
      >
        {processGroups?.results?.length && buildTree(processGroups.results)}
      </SimpleTreeView>
    </Paper>
  );
}

// const CustomTreeItem = React.forwardRef(function CustomTreeItem(
//     props: StyledTreeItemProps,
//     ref: React.Ref<HTMLLIElement>,
//   ) {
//     const theme = useTheme();
//     const {
//       id,
//       itemId,
//       label,
//       disabled,
//       children,
//       bgColor,
//       color,
//       labelIcon: LabelIcon,
//       labelInfo,
//       colorForDarkMode,
//       bgColorForDarkMode,
//       ...other
//     } = props;

//     const {
//       getRootProps,
//       getContentProps,
//       getIconContainerProps,
//       getLabelProps,
//       getGroupTransitionProps,
//       status,
//     } = useTreeItem({ id, itemId, children, label, disabled, rootRef: ref });

//     const style = {
//       '--tree-view-color': theme.palette.mode !== 'dark' ? color : colorForDarkMode,
//       '--tree-view-bg-color':
//         theme.palette.mode !== 'dark' ? bgColor : bgColorForDarkMode,
//     };

//     return (
//       <TreeItem2Provider itemId={itemId}>
//         <CustomTreeItemRoot {...getRootProps({ ...other, style })}>
//           <CustomTreeItemContent
//             {...getContentProps({
//               className: clsx('content', {
//                 expanded: status.expanded,
//                 selected: status.selected,
//                 focused: status.focused,
//               }),
//             })}
//           >
//             <CustomTreeItemIconContainer {...getIconContainerProps()}>
//               <TreeItem2Icon status={status} />
//             </CustomTreeItemIconContainer>
//             <Box
//               sx={{
//                 display: 'flex',
//                 flexGrow: 1,
//                 alignItems: 'center',
//                 p: 0.5,
//                 pr: 0,
//               }}
//             >
//               <Box component={LabelIcon} color="inherit" sx={{ mr: 1 }} />
//               <Typography
//                 {...getLabelProps({
//                   variant: 'body2',
//                   sx: { display: 'flex', fontWeight: 'inherit', flexGrow: 1 },
//                 })}
//               />
//               <Typography variant="caption" color="inherit">
//                 {labelInfo}
//               </Typography>
//             </Box>
//           </CustomTreeItemContent>
//           {children && (
//             <CustomTreeItemGroupTransition {...getGroupTransitionProps()} />
//           )}
//         </CustomTreeItemRoot>
//       </TreeItem2Provider>
//     );
//   });
