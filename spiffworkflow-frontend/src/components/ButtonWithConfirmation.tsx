import { useState } from 'react';
// @ts-ignore
import { Button, Modal } from '@carbon/react';

type OwnProps = {
  'data-qa'?: string;
  description?: string;
  buttonLabel?: string;
  onConfirmation: (..._args: any[]) => any;
  title?: string;
  confirmButtonLabel?: string;
  kind?: string;
  renderIcon?: Element;
  iconDescription?: string | null;
  hasIconOnly?: boolean;
  classNameForModal?: string;
};

export default function ButtonWithConfirmation({
  description,
  buttonLabel,
  onConfirmation,
  'data-qa': dataQa,
  title = 'Are you sure?',
  confirmButtonLabel = 'OK',
  kind = 'danger',
  renderIcon,
  iconDescription = null,
  hasIconOnly = false,
  classNameForModal,
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
        data-qa={`${dataQa}-modal-confirmation-dialog`}
        modalHeading={description}
        modalLabel={title}
        primaryButtonText={confirmButtonLabel}
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleConfirmationPromptCancel}
        onRequestSubmit={handleConfirmation}
        onRequestClose={handleConfirmationPromptCancel}
        className={classNameForModal}
      />
    );
  };

  return (
    <>
      <Button
        data-qa={dataQa}
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
