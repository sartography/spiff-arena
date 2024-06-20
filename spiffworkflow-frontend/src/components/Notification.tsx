import React, { useState } from 'react';
import {
  Close,
  Checkmark,
  Error,
  // @ts-ignore
  WarningAlt,
} from '@carbon/icons-react';
// @ts-ignore
import { Button } from '@carbon/react';
import { ObjectWithStringKeysAndValues } from '../interfaces';

type OwnProps = {
  title: string;
  children?: React.ReactNode;
  onClose?: Function;
  type?: string;
  hideCloseButton?: boolean;
  allowTogglingFullMessage?: boolean;
  timeout?: number;
  withBottomMargin?: boolean;
  'data-qa'?: string;
};

export function Notification({
  title,
  children,
  onClose,
  type = 'success',
  hideCloseButton = false,
  allowTogglingFullMessage = false,
  timeout,
  withBottomMargin = true,
  'data-qa': dataQa,
}: OwnProps) {
  const [showMessage, setShowMessage] = useState<boolean>(
    !allowTogglingFullMessage,
  );
  let iconComponent = <Checkmark className="notification-icon" />;
  if (type === 'error') {
    iconComponent = <Error className="notification-icon" />;
  } else if (type === 'warning') {
    iconComponent = <WarningAlt className="notification-icon" />;
  }

  if (timeout && onClose) {
    setTimeout(() => {
      onClose();
    }, timeout);
  }

  let classes = `cds--inline-notification cds--inline-notification--low-contrast cds--inline-notification--${type}`;
  if (withBottomMargin) {
    classes = `${classes} with-bottom-margin`;
  }

  const additionalProps: ObjectWithStringKeysAndValues = {};
  if (dataQa) {
    additionalProps['data-qa'] = dataQa;
  }

  return (
    // we control the props added to the variable so we know it's fine
    // eslint-disable-next-line react/jsx-props-no-spreading
    <div role="status" className={classes} {...additionalProps}>
      <div className="cds--inline-notification__details">
        <div className="cds--inline-notification__text-wrapper">
          {iconComponent}
          <div className="cds--inline-notification__title">{title}</div>
          {showMessage ? (
            <div className="cds--inline-notification__subtitle">{children}</div>
          ) : null}
        </div>
      </div>
      {hideCloseButton ? null : (
        <Button
          data-qa="close-publish-notification"
          renderIcon={Close}
          iconDescription="Close Notification"
          className="cds--inline-notification__close-button"
          hasIconOnly
          size="sm"
          kind="ghost"
          onClick={onClose}
        />
      )}
      {allowTogglingFullMessage ? (
        <Button
          data-qa="close-publish-notification"
          className="cds--inline-notification__close-button"
          size="sm"
          kind="ghost"
          onClick={() => setShowMessage(!showMessage)}
        >
          {showMessage ? 'Hide' : 'Details'}&nbsp;
        </Button>
      ) : null}
    </div>
  );
}
