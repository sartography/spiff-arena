import { IconButton } from '@mui/material';
import { useConfirmationDialog } from '../hooks/useConfirmationDialog';
import SpiffTooltip from './SpiffTooltip';

interface ConfirmIconButtonProps {
  'data-testid'?: string;
  renderIcon: React.ReactNode;
  iconDescription: string;
  onConfirmation: () => void;
  title?: string;
  description?: string;
  confirmButtonLabel?: string;
  color?: 'inherit' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
  disabled?: boolean;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
}

export default function ConfirmIconButton({
  'data-testid': dataTestid,
  renderIcon,
  iconDescription,
  onConfirmation,
  title,
  description,
  confirmButtonLabel,
  color = 'error',
  disabled = false,
  tooltipPlacement = 'top',
}: ConfirmIconButtonProps) {
  const { openConfirmation, ConfirmationDialog } = useConfirmationDialog(
    onConfirmation,
    {
      title,
      description,
      confirmText: confirmButtonLabel,
      confirmColor: color,
    }
  );

  return (
    <>
      <SpiffTooltip title={iconDescription} placement={tooltipPlacement}>
        <IconButton
          data-testid={dataTestid}
          onClick={openConfirmation}
          aria-label={iconDescription}
          disabled={disabled}
        >
          {renderIcon}
        </IconButton>
      </SpiffTooltip>
      <ConfirmationDialog />
    </>
  );
}