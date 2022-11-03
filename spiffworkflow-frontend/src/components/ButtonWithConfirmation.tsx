import { useState } from 'react';
// @ts-ignore
import { Button, Modal } from '@carbon/react';

type OwnProps = {
  description?: string;
  buttonLabel: string;
  onConfirmation: (..._args: any[]) => any;
  title?: string;
  confirmButtonLabel?: string;
};

export default function ButtonWithConfirmation({
  description,
  buttonLabel,
  onConfirmation,
  title = 'Are you sure?',
  confirmButtonLabel = 'OK',
}: OwnProps) {
  const [showConfirmationPrompt, setShowConfirmationPrompt] = useState(false);

  const handleShowConfirmationPrompt = () => {
    setShowConfirmationPrompt(true);
  };
  const handleConfirmationPromptCancel = () => {
    setShowConfirmationPrompt(false);
  };

  const modalBodyElement = () => {
    if (description) {
      return <Modal.Body>{description}</Modal.Body>;
    }
    return null;
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
        modalHeading={description}
        modalLabel={title}
        primaryButtonText={confirmButtonLabel}
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleConfirmationPromptCancel}
        onRequestSubmit={handleConfirmation}
      />
    );
    // return (
    //   <Modal
    //     show={showConfirmationPrompt}
    //     onHide={handleConfirmationPromptCancel}
    //   >
    //     <Modal.Header closeButton>
    //       <Modal.Title>{title}</Modal.Title>
    //     </Modal.Header>
    //     {modalBodyElement()}
    //     <Modal.Footer>
    //       <Button variant="secondary" onClick={handleConfirmationPromptCancel}>
    //         Cancel
    //       </Button>
    //       <Button variant="primary" onClick={handleConfirmation}>
    //         {confirmButtonLabel}
    //       </Button>
    //     </Modal.Footer>
    //   </Modal>
    // );
  };

  return (
    <>
      <Button onClick={handleShowConfirmationPrompt} variant="danger">
        {buttonLabel}
      </Button>
      {confirmationDialog()}
    </>
  );
}
