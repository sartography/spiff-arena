import React from 'react';
import {
  FormContextType,
  IconButtonProps,
  RJSFSchema,
  StrictRJSFSchema,
} from '@rjsf/utils';

// @ts-ignore
import { Add, TrashCan, ArrowUp, ArrowDown } from '@carbon/icons-react';

export default function IconButton<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any
>(props: IconButtonProps<T, S, F>) {
  const {
    iconType = 'default',
    icon,
    className,
    uiSchema,
    registry,
    ...otherProps
  } = props;
  // icon string optios: plus, remove, arrow-up, arrow-down
  let carbonIcon = (
    <p>
      Add new <Add />
    </p>
  );
  if (icon === 'remove') {
    carbonIcon = <TrashCan />;
  }
  if (icon === 'arrow-up') {
    carbonIcon = <ArrowUp />;
  }
  if (icon === 'arrow-down') {
    carbonIcon = <ArrowDown />;
  }

  return (
    <button
      type="button"
      className={`btn btn-${iconType} ${className}`}
      {...otherProps}
    >
      {carbonIcon}
    </button>
  );
}

export function MoveDownButton<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any
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
  F extends FormContextType = any
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
  F extends FormContextType = any
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
