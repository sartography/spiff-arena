import { createContext } from 'react';
import { AbilityBuilder, Ability } from '@casl/ability';
import { createContextualCan } from '@casl/react';

export const AbilityContext = createContext(new Ability());
export const Can = createContextualCan(AbilityContext.Consumer);
