import { Button } from '@mui/material';
import { useConfirmationDialog } from '../hooks/useConfirmationDialog';

interface ConfirmButtonProps {
  'data-testid'?: string;
  buttonLabel: string;
  onConfirmation: () => void;
  title?: string;
  description?: string;
  confirmButtonLabel?: string;
  variant?: 'text' | 'outlined' | 'contained';
  color?:
    | 'inherit'
    | 'primary'
    | 'secondary'
    | 'success'
    | 'error'
    | 'info'
    | 'warning';
  startIcon?: React.ReactNode;
  disabled?: boolean;
}

export default function ConfirmButton({
  'data-testid': dataTestid,
  buttonLabel,
  onConfirmation,
  title,
  description,
  confirmButtonLabel,
  variant = 'contained',
  color = 'error',
  startIcon,
  disabled = false,
}: ConfirmButtonProps) {
  const { openConfirmation, ConfirmationDialog } = useConfirmationDialog(
    onConfirmation,
    {
      title,
      description,
      confirmText: confirmButtonLabel,
      confirmColor: color,
    },
  );

  return (
    <>
      <Button
        data-testid={dataTestid}
        onClick={openConfirmation}
        variant={variant}
        color={color}
        startIcon={startIcon}
        disabled={disabled}
      >
        {buttonLabel}
      </Button>
      <ConfirmationDialog />
    </>
  );
}
