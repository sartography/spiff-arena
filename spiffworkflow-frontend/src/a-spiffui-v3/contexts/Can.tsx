import { createContext } from 'react';
import { Ability } from '@casl/ability';
import { createContextualCan } from '@casl/react';

export const AbilityContext = createContext(new Ability());
export const Can = createContextualCan(AbilityContext.Consumer);
