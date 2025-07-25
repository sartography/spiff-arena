// from https://raw.githubusercontent.com/arthurtyukayev/use-keyboard-shortcut/develop/lib/useKeyboardShortcut.js
import { useEffect, useCallback, useRef, useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { KeyboardShortcuts } from '../interfaces';

export const overrideSystemHandling = (e: KeyboardEvent) => {
  if (e) {
    if (e.preventDefault) {
      e.preventDefault();
    }
    if (e.stopPropagation) {
      e.stopPropagation();
    }
  }
};

export const uniqFast = (a: any[]) => {
  return [...new Set(a)];
};

const EXCLUDE_LIST_DOM_TARGETS = ['TEXTAREA', 'INPUT'];

const DEFAULT_OPTIONS = {
  ignoreInputFields: true,
};

const useKeyboardShortcut = (
  keyboardShortcuts: KeyboardShortcuts,
  userOptions?: any,
) => {
  let options = DEFAULT_OPTIONS;
  if (userOptions) {
    options = { ...options, ...userOptions };
  }

  const [helpControlOpen, setHelpControlOpen] = useState<boolean>(false);

  // useRef to avoid a constant re-render on keydown and keyup.
  const keySequence = useRef<string[]>([]);

  const shortcutKeys = Object.keys(keyboardShortcuts);
  const lengthsOfShortcutKeys = shortcutKeys.map(
    (shortcutKey: string) => shortcutKey.length,
  );
  const numberOfKeysToKeep = Math.max(...lengthsOfShortcutKeys);

  const openKeyboardShortcutHelpControl = useCallback(() => {
    const keyboardShortcutList = shortcutKeys.map((key: string) => {
      return (
        <p>
          <div className="shortcut-description">
            {keyboardShortcuts[key].label}:{' '}
          </div>
          <div className="shortcut-key-group">
            {key.split(',').map((keyString) => (
              <span className="shortcut-key">{keyString}</span>
            ))}
          </div>
        </p>
      );
    });

    return (
      <Dialog
        open={helpControlOpen}
        onClose={() => setHelpControlOpen(false)}
        maxWidth="sm"
      >
        <DialogTitle>Keyboard shortcuts</DialogTitle>
        <DialogContent>
          <p>
            <div className="shortcut-description">
              Open keyboard shortcut help control:
            </div>
            <div className="shortcut-key-group">
              <span className="shortcut-key">Shift</span>
              <span className="shortcut-key">?</span>
            </div>
          </p>
          {keyboardShortcutList}
        </DialogContent>
      </Dialog>
    );
  }, [keyboardShortcuts, helpControlOpen, shortcutKeys]);

  const keydownListener = useCallback(
    (keydownEvent: KeyboardEvent) => {
      if (keydownEvent.key === '?' && keydownEvent.shiftKey) {
        overrideSystemHandling(keydownEvent);
        keySequence.current = [];
        setHelpControlOpen(true);
        return false;
      }
      if (
        keydownEvent.ctrlKey ||
        keydownEvent.shiftKey ||
        keydownEvent.altKey
      ) {
        return undefined;
      }
      const loweredKey = String(keydownEvent.key).toLowerCase();

      if (
        options.ignoreInputFields &&
        EXCLUDE_LIST_DOM_TARGETS.indexOf(
          (keydownEvent.target as any).tagName,
        ) >= 0
      ) {
        return undefined;
      }

      keySequence.current.push(loweredKey);
      const keySequenceString = keySequence.current.join(',');
      const shortcutKey = shortcutKeys.find((sk: string) =>
        keySequenceString.endsWith(sk),
      );

      if (shortcutKey) {
        overrideSystemHandling(keydownEvent);
        keySequence.current = [];
        keyboardShortcuts[shortcutKey].function();
        return false;
      }

      if (keySequence.current.length >= numberOfKeysToKeep) {
        keySequence.current.shift();
      }

      return false;
    },
    [
      options.ignoreInputFields,
      keyboardShortcuts,
      numberOfKeysToKeep,
      shortcutKeys,
    ],
  );

  useEffect(() => {
    window.addEventListener('keydown', keydownListener);
    return () => {
      window.removeEventListener('keydown', keydownListener);
    };
  }, [keydownListener]);

  return openKeyboardShortcutHelpControl();
};

export default useKeyboardShortcut;
