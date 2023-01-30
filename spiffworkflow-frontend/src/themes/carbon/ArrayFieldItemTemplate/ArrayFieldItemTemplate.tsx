import React, { CSSProperties } from 'react';
import {
  ArrayFieldTemplateItemType,
  FormContextType,
  RJSFSchema,
  StrictRJSFSchema,
} from '@rjsf/utils';
import {
  Grid,
  Column,
  // @ts-ignore
} from '@carbon/react';

/** The `ArrayFieldItemTemplate` component is the template used to render an items of an array.
 *
 * @param props - The `ArrayFieldTemplateItemType` props for the component
 */
export default function ArrayFieldItemTemplate<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any
>(props: ArrayFieldTemplateItemType<T, S, F>) {
  const {
    children,
    className,
    disabled,
    hasToolbar,
    hasMoveDown,
    hasMoveUp,
    hasRemove,
    index,
    onDropIndexClick,
    onReorderClick,
    readonly,
    registry,
    uiSchema,
  } = props;
  const { MoveDownButton, MoveUpButton, RemoveButton } =
    registry.templates.ButtonTemplates;
  const btnStyle: CSSProperties = {
    marginBottom: '0.5em',
  };
  const mainColumnWidthSmall = 3;
  const mainColumnWidthMedium = 4;
  const mainColumnWidthLarge = 7;
  return (
    <div className={className}>
      <Grid condensed fullWidth>
        <Column
          sm={mainColumnWidthSmall}
          md={mainColumnWidthMedium}
          lg={mainColumnWidthLarge}
        >
          {children}
        </Column>
        {hasToolbar && (
          <Column sm={1} md={1} lg={1}>
            <div className="array-item-toolbox">
              <div className="NOT-btn-group">
                {(hasMoveUp || hasMoveDown) && (
                  <MoveUpButton
                    style={btnStyle}
                    disabled={disabled || readonly || !hasMoveUp}
                    onClick={onReorderClick(index, index - 1)}
                    uiSchema={uiSchema}
                    registry={registry}
                  />
                )}
                {(hasMoveUp || hasMoveDown) && (
                  <MoveDownButton
                    style={btnStyle}
                    disabled={disabled || readonly || !hasMoveDown}
                    onClick={onReorderClick(index, index + 1)}
                    uiSchema={uiSchema}
                    registry={registry}
                  />
                )}
                {hasRemove && (
                  <RemoveButton
                    style={btnStyle}
                    disabled={disabled || readonly}
                    onClick={onDropIndexClick(index)}
                    uiSchema={uiSchema}
                    registry={registry}
                  />
                )}
              </div>
            </div>
          </Column>
        )}
      </Grid>
    </div>
  );
}
