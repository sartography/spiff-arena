import React from 'react';
import { Button } from '@carbon/react';
import {
  FormContextType,
  IconButtonProps,
  RJSFSchema,
  StrictRJSFSchema,
} from '@rjsf/utils';

import RemoveIcon from '@mui/icons-material/Remove';
import { IconButton as MuiIconButton } from '@mui/material';

import { Add, TrashCan, ArrowUp, ArrowDown } from '@carbon/icons-react';

export default function IconButton<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: IconButtonProps<T, S, F>) {
  const {
    iconType = 'default',
    icon,
    className,
    uiSchema,
    registry,
    title,
    ...otherProps
  } = props;
  // icon string optios: plus, remove, arrow-up, arrow-down
  let carbonIcon = Add;
  if (icon === 'remove') {
    carbonIcon = TrashCan;
  }
  if (icon === 'arrow-up') {
    carbonIcon = ArrowUp;
  }
  if (icon === 'arrow-down') {
    carbonIcon = ArrowDown;
  }
  if (icon === 'core-remove') {
    carbonIcon = RemoveIcon;
  }

  return (
    <Button
      className={`btn btn-${iconType} ${className}`}
      iconDescription={title}
      kind="tertiary"
      title={null}
      hasIconOnly
      size="sm"
      renderIcon={carbonIcon}
      {...otherProps}
    />
  );
}

export function MoveDownButton<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: IconButtonProps<T, S, F>) {
  return (
    <IconButton
      title="Move down"
      className="array-item-move-down"
      {...props}
      icon="arrow-down"
    />
  );
}

export function MoveUpButton<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: IconButtonProps<T, S, F>) {
  return (
    <IconButton
      title="Move up"
      className="array-item-move-up"
      {...props}
      icon="arrow-up"
    />
  );
}

export function RemoveButton<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: IconButtonProps<T, S, F>) {
  return (
    <IconButton
      title="Remove"
      className="array-item-remove"
      {...props}
      iconType="danger"
      icon="remove"
    />
  );
}

export function MuiRemoveButton<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: IconButtonProps<T, S, F>) {
  return (
    <MuiIconButton
      title="Remove"
      {...props}
      color="warning"
      aria-label="Remove"
    >
      <RemoveIcon />
    </MuiIconButton>
  );
}
