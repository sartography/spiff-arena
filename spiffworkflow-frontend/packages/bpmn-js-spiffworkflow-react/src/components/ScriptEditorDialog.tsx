import React, { ReactNode, SyntheticEvent } from 'react';
import { Box, Button, Tab, Tabs } from '@mui/material';
import DialogShell from './DialogShell';

type ScriptEditorDialogProps = {
    open: boolean;
    title: string;
    tabValue: number;
    onTabChange: (event: SyntheticEvent, value: number) => void;
    scriptTabLabel: string;
    unitTestsTabLabel: string;
    assistTabLabel?: string;
    assistEnabled?: boolean;
    renderScript: () => ReactNode;
    renderUnitTests?: () => ReactNode;
    renderAssist?: () => ReactNode;
    closeLabel: string;
    onClose: () => void;
};

function TabPanel(props: {
    children?: ReactNode;
    index: number;
    value: number;
}) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`simple-tabpanel-${index}`}
            aria-labelledby={`simple-tab-${index}`}
            {...other}
        >
            {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
        </div>
    );
}

export default function ScriptEditorDialog({
    open,
    title,
    tabValue,
    onTabChange,
    scriptTabLabel,
    unitTestsTabLabel,
    assistTabLabel,
    assistEnabled = false,
    renderScript,
    renderUnitTests,
    renderAssist,
    closeLabel,
    onClose,
}: ScriptEditorDialogProps) {
    return (
        <DialogShell
            className="bpmn-editor-wide-dialog"
            open={open}
            onClose={onClose}
            title={title}
        >
            <Tabs value={tabValue} onChange={onTabChange}>
                <Tab label={scriptTabLabel} />
                {assistEnabled && assistTabLabel ? (
                    <Tab label={assistTabLabel} />
                ) : null}
                {renderUnitTests ? <Tab label={unitTestsTabLabel} /> : null}
            </Tabs>
            <Box>
                <TabPanel value={tabValue} index={0}>
                    {renderScript()}
                </TabPanel>
                {assistEnabled && assistTabLabel && renderAssist ? (
                    <TabPanel value={tabValue} index={1}>
                        {renderAssist()}
                    </TabPanel>
                ) : null}
                {renderUnitTests ? (
                    <TabPanel value={tabValue} index={assistEnabled && assistTabLabel ? 2 : 1}>
                        {renderUnitTests()}
                    </TabPanel>
                ) : null}
            </Box>
            <Button onClick={onClose}>{closeLabel}</Button>
        </DialogShell>
    );
}
