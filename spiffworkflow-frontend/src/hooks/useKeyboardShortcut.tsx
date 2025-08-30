// from https://raw.githubusercontent.com/arthurtyukayev/use-keyboard-shortcut/develop/lib/useKeyboardShortcut.js
import { useEffect, useCallback, useRef, useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
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
    const keyboardShortcutList = shortcutKeys.map(
      (key: string, index: number) => {
        return (
          <Box
            key={index}
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              py: 1,
              borderBottom:
                index < shortcutKeys.length - 1 ? '1px solid #eee' : 'none',
            }}
          >
            <Typography variant="body1">
              {keyboardShortcuts[key].label}
            </Typography>
            <Stack direction="row" spacing={1}>
              {key.split(',').map((keyString, keyIndex) => (
                <Chip
                  key={keyIndex}
                  label={keyString}
                  size="small"
                  variant="outlined"
                  sx={{
                    fontFamily: 'monospace',
                    fontWeight: 'bold',
                    textTransform: 'capitalize',
                  }}
                />
              ))}
            </Stack>
          </Box>
        );
      },
    );

    return (
      <Dialog
        open={helpControlOpen}
        onClose={() => setHelpControlOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Typography variant="h6" component="div">
            Keyboard Shortcuts
          </Typography>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ mb: 2 }}>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                py: 1,
                borderBottom: '1px solid #eee',
              }}
            >
              <Typography variant="body1">
                Open keyboard shortcut help
              </Typography>
              <Stack direction="row" spacing={1}>
                <Chip
                  label="Shift"
                  size="small"
                  variant="outlined"
                  sx={{
                    fontFamily: 'monospace',
                    fontWeight: 'bold',
                  }}
                />
                <Chip
                  label="?"
                  size="small"
                  variant="outlined"
                  sx={{
                    fontFamily: 'monospace',
                    fontWeight: 'bold',
                  }}
                />
              </Stack>
            </Box>
          </Box>
          {keyboardShortcutList}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHelpControlOpen(false)}>Close</Button>
        </DialogActions>
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
