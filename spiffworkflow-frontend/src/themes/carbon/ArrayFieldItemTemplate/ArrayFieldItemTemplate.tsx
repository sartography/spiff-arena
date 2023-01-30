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
  const mainColumnWidthSmall = hasToolbar ? 3 : 4;
  const mainColumnWidthMedium = hasToolbar ? 6 : 8;
  const mainColumnWidthLarge = hasToolbar ? 12 : 16;
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
          <Column
            sm={4 - mainColumnWidthSmall}
            md={8 - mainColumnWidthMedium}
            lg={16 - mainColumnWidthLarge}
          >
            <div className="array-item-toolbox">
              <div className="NOT-btn-group">
                <div>
                  {(hasMoveUp || hasMoveDown) && (
                    <MoveUpButton
                      style={btnStyle}
                      disabled={disabled || readonly || !hasMoveUp}
                      onClick={onReorderClick(index, index - 1)}
                      uiSchema={uiSchema}
                      registry={registry}
                    />
                  )}
                </div>
                <div>
                  {(hasMoveUp || hasMoveDown) && (
                    <MoveDownButton
                      style={btnStyle}
                      disabled={disabled || readonly || !hasMoveDown}
                      onClick={onReorderClick(index, index + 1)}
                      uiSchema={uiSchema}
                      registry={registry}
                    />
                  )}
                </div>
                <div>
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
            </div>
          </Column>
        )}
      </Grid>
    </div>
  );
}
