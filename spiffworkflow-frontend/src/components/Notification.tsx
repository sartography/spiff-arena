import React from 'react';
import {
  Close,
  Checkmark,
  Error,
  // @ts-ignore
} from '@carbon/icons-react';
// @ts-ignore
import { Button } from '@carbon/react';

type OwnProps = {
  title: string;
  children?: React.ReactNode;
  onClose: Function;
  type?: string;
};

export function Notification({
  title,
  children,
  onClose,
  type = 'success',
}: OwnProps) {
  let iconComponent = <Checkmark className="notification-icon" />;
  if (type === 'error') {
    iconComponent = <Error className="notification-icon" />;
  }
  return (
    <div
      role="status"
      className={`with-bottom-margin cds--inline-notification cds--inline-notification--low-contrast cds--inline-notification--${type}`}
    >
      <div className="cds--inline-notification__details">
        <div className="cds--inline-notification__text-wrapper">
          {iconComponent}
          <div className="cds--inline-notification__title">{title}</div>
          <div className="cds--inline-notification__subtitle">{children}</div>
        </div>
      </div>
      <Button
        data-qa="close-publish-notification"
        renderIcon={Close}
        iconDescription="Close Notification"
        className="cds--inline-notification__close-button"
        hasIconOnly
        size="sm"
        kind=""
        onClick={onClose}
      />
    </div>
  );
}
