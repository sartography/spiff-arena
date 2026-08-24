import { createContext, type ReactNode } from 'react';
import { Ability } from '@casl/ability';
import { AbilityProvider, Can as CaslCan } from '@casl/react';

export type AppAbility = Ability<[string, string]>;

export const createAppAbility = () => new Ability<[string, string]>();

export const AbilityContext = createContext<AppAbility>(createAppAbility());

type CanProps = {
  I?: string;
  do?: string;
  a?: string;
  an?: string;
  on?: string;
  not?: boolean;
  passThrough?: boolean;
  field?: string;
  ability?: AppAbility;
  children: ReactNode | ((isAllowed: boolean) => ReactNode);
};

export function Can({ ability, children, ...props }: CanProps) {
  const caslChildren =
    typeof children === 'function'
      ? (exposes: { isAllowed: boolean }) => children(exposes.isAllowed)
      : children;

  const canComponent = (
    <CaslCan {...(props as any)} passThrough={props.passThrough}>
      {caslChildren as ReactNode}
    </CaslCan>
  );

  if (!ability) {
    return canComponent;
  }

  return <AbilityProvider value={ability}>{canComponent}</AbilityProvider>;
}
