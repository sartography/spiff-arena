import React from 'react';
import { getTemplate, WidgetProps } from '@rjsf/utils';

function DateWidget(props: WidgetProps) {
  const { options, registry } = props;
  const BaseInputTemplate = getTemplate<'BaseInputTemplate'>(
    'BaseInputTemplate',
    registry,
    options
  );

  return (
    <BaseInputTemplate
      type="date"
      dateFormat="Y-m-d"
      InputLabelProps={{
        shrink: true,
      }}
      {...props}
    />
  );
}

export default DateWidget;
