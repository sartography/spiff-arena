import { Dialog, DialogContent, DialogTitle } from '@mui/material';
import { useTranslation } from 'react-i18next';
import {
  childrenForErrorObject,
  errorForDisplayFromString,
} from '../ErrorDisplay';
import { ProcessData } from '../../interfaces';

type ProcessDataDialogProps = {
  processData: ProcessData | null;
  onClose: () => void;
};

export default function ProcessDataDialog({
  processData,
  onClose,
}: ProcessDataDialogProps) {
  const { t } = useTranslation();
  if (!processData) {
    return null;
  }

  const body =
    processData.authorized === false ? (
      <>
        {childrenForErrorObject(
          errorForDisplayFromString(processData.process_data_value),
          t,
        )}
      </>
    ) : (
      <>
        <p>{t('value')}:</p>
        <pre>{JSON.stringify(processData.process_data_value)}</pre>
      </>
    );

  return (
    <Dialog className="wide-dialog" open onClose={onClose}>
      <DialogTitle>
        {t('process_data_object', {
          identifier: processData.process_data_identifier,
        })}
      </DialogTitle>
      <DialogContent>{body}</DialogContent>
    </Dialog>
  );
}
