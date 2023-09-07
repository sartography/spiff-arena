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
  const mainColumnWidthSmall = 2;
  const mainColumnWidthMedium = 3;
  const mainColumnWidthLarge = 6;
  return (
    <div className={className}>
      <Grid condensed fullWidth>
        <Column sm={1} md={1} lg={1}>
          { /* This column is empty on purpose, it helps shift the content and overcomes an abundance of effort
            to keep grid content to be pushed hard to left at all times, and in this we really need a slight
            indentation, at least, I felt so at the time.  Could change my mind, as likely as not. */ }
        </Column>
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
