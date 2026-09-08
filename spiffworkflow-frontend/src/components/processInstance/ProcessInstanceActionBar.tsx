import {
  DeleteOutlineOutlined,
  LinkOutlined,
  PauseOutlined,
  PlayArrow,
  StopCircleOutlined,
  SyncAltOutlined,
} from '@mui/icons-material';
import { IconButton } from '@mui/material';
import { useTranslation } from 'react-i18next';
import ProcessInstanceClass from '../../classes/ProcessInstanceClass';
import { ProcessInstance } from '../../interfaces';
import ConfirmIconButton from '../ConfirmIconButton';
import { Notification } from '../Notification';
import SpiffTooltip from '../SpiffTooltip';

type ProcessInstanceActionBarProps = {
  processInstance: ProcessInstance;
  canDelete: boolean;
  canMigrate: boolean;
  canResume: boolean;
  canSuspend: boolean;
  canTerminate: boolean;
  copiedShortLinkToClipboard: boolean;
  onCopyShortLink: () => void;
  onCopiedNotificationClose: () => void;
  onDelete: () => void;
  onMigrate: () => void;
  onResume: () => void;
  onSuspend: () => void;
  onTerminate: () => void;
};

export default function ProcessInstanceActionBar({
  processInstance,
  canDelete,
  canMigrate,
  canResume,
  canSuspend,
  canTerminate,
  copiedShortLinkToClipboard,
  onCopyShortLink,
  onCopiedNotificationClose,
  onDelete,
  onMigrate,
  onResume,
  onSuspend,
  onTerminate,
}: ProcessInstanceActionBarProps) {
  const { t } = useTranslation();
  const isSuspended = processInstance.status === 'suspended';
  const isTerminal = ProcessInstanceClass.terminalStatuses().includes(
    processInstance.status,
  );
  const canSuspendStatus = !ProcessInstanceClass.nonErrorTerminalStatuses()
    .concat(['suspended'])
    .includes(processInstance.status);

  return (
    <>
      <SpiffTooltip title={t('copy_shareable_link_tooltip')} placement="top">
        <IconButton
          onClick={onCopyShortLink}
          aria-label={t('copy_shareable_link_tooltip')}
        >
          <LinkOutlined />
        </IconButton>
      </SpiffTooltip>
      {canTerminate && !isTerminal ? (
        <ConfirmIconButton
          renderIcon={<StopCircleOutlined />}
          iconDescription={t('terminate_button')}
          description={t('terminate_process_instance', {
            id: processInstance.id,
          })}
          onConfirmation={onTerminate}
          confirmButtonLabel={t('terminate_button')}
        />
      ) : null}
      {canSuspend && canSuspendStatus ? (
        <SpiffTooltip title={t('suspend_tooltip')} placement="top">
          <IconButton onClick={onSuspend} aria-label={t('suspend_tooltip')}>
            <PauseOutlined />
          </IconButton>
        </SpiffTooltip>
      ) : null}
      {canMigrate && isSuspended ? (
        <SpiffTooltip title={t('migrate')} placement="top">
          <IconButton onClick={onMigrate} aria-label={t('migrate')}>
            <SyncAltOutlined />
          </IconButton>
        </SpiffTooltip>
      ) : null}
      {canResume && isSuspended ? (
        <SpiffTooltip title={t('resume')} placement="top">
          <IconButton onClick={onResume} aria-label={t('resume')}>
            <PlayArrow />
          </IconButton>
        </SpiffTooltip>
      ) : null}
      {canDelete && isTerminal ? (
        <ConfirmIconButton
          data-testid="process-instance-delete"
          renderIcon={<DeleteOutlineOutlined />}
          iconDescription={t('delete')}
          description={t('delete_process_instance', { id: processInstance.id })}
          onConfirmation={onDelete}
          confirmButtonLabel={t('delete')}
        />
      ) : null}
      {copiedShortLinkToClipboard ? (
        <Notification
          onClose={onCopiedNotificationClose}
          type="success"
          title={t('copied_link_to_clipboard')}
          timeout={3000}
          hideCloseButton
          withBottomMargin={false}
        />
      ) : null}
    </>
  );
}
