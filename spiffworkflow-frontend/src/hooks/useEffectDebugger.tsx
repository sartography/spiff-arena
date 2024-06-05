import { useEffect, useRef } from 'react';

// https://stackoverflow.com/a/59843241/6090676
// useful for determining what state has changed that caused useEffect to trigger.
// just change the useEffect in question to useEffectDebugger
const usePrevious = (value: any, initialValue: any) => {
  const ref = useRef(initialValue);
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
};
export default function useEffectDebugger(
  effectHook: any,
  dependencies: any,
  dependencyNames: any = [],
) {
  const previousDeps = usePrevious(dependencies, []);

  const changedDeps = dependencies.reduce(
    (accum: any, dependency: any, index: any) => {
      if (dependency !== previousDeps[index]) {
        const keyName = dependencyNames[index] || index;
        return {
          ...accum,
          [keyName]: {
            before: previousDeps[index],
            after: dependency,
          },
        };
      }

      return accum;
    },
    {},
  );

  if (Object.keys(changedDeps).length) {
    console.log('[use-effect-debugger] ', changedDeps);
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(effectHook, dependencies);
}
