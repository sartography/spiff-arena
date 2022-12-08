import React from 'react';
// @ts-ignore
import { Close, CheckmarkFilled } from '@carbon/icons-react';
// @ts-ignore
import { Button } from '@carbon/react';

type OwnProps = {
  title: string;
  children: React.ReactNode;
  onClose: (..._args: any[]) => any;
  type?: string;
};

export function Notification({
  title,
  children,
  onClose,
  type = 'success',
}: OwnProps) {
  let iconClassName = 'green-icon';
  if (type === 'error') {
    iconClassName = 'red-icon';
  }
  return (
    <div
      role="status"
      className={`with-bottom-margin cds--inline-notification cds--inline-notification--low-contrast cds--inline-notification--${type}`}
    >
      <div className="cds--inline-notification__details">
        <div className="cds--inline-notification__text-wrapper">
          <CheckmarkFilled className={`${iconClassName} notification-icon`} />
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
