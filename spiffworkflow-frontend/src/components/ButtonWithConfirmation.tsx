import { useState } from 'react';
// @ts-ignore
import { Button, Modal } from '@carbon/react';

type OwnProps = {
  description?: string;
  buttonLabel?: string;
  onConfirmation: (..._args: any[]) => any;
  title?: string;
  confirmButtonLabel?: string;
  kind?: string;
  renderIcon?: boolean;
  iconDescription?: string | null;
  hasIconOnly?: boolean;
};

export default function ButtonWithConfirmation({
  description,
  buttonLabel,
  onConfirmation,
  title = 'Are you sure?',
  confirmButtonLabel = 'OK',
  kind = 'danger',
  renderIcon = false,
  iconDescription = null,
  hasIconOnly = false,
}: OwnProps) {
  const [showConfirmationPrompt, setShowConfirmationPrompt] = useState(false);

  const handleShowConfirmationPrompt = () => {
    setShowConfirmationPrompt(true);
  };
  const handleConfirmationPromptCancel = () => {
    setShowConfirmationPrompt(false);
  };

  const handleConfirmation = () => {
    onConfirmation();
    setShowConfirmationPrompt(false);
  };

  const confirmationDialog = () => {
    return (
      <Modal
        open={showConfirmationPrompt}
        danger
        data-qa="modal-confirmation-dialog"
        modalHeading={description}
        modalLabel={title}
        primaryButtonText={confirmButtonLabel}
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleConfirmationPromptCancel}
        onRequestSubmit={handleConfirmation}
      />
    );
  };

  return (
    <>
      <Button
        onClick={handleShowConfirmationPrompt}
        kind={kind}
        renderIcon={renderIcon}
        iconDescription={iconDescription}
        hasIconOnly={hasIconOnly}
      >
        {buttonLabel}
      </Button>
      {confirmationDialog()}
    </>
  );
}
