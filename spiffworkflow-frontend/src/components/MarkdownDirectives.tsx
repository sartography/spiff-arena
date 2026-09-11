import { ComponentProps, ReactNode, useId, useState } from 'react';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import MDEditor from '@uiw/react-md-editor';
import remarkDirective from 'remark-directive';
import { toString } from 'mdast-util-to-string';
import { SKIP, visit } from 'unist-util-visit';
import type { Root } from 'mdast';
import type { VFile } from 'vfile';

type MarkdownOptions = ComponentProps<typeof MDEditor.Markdown>;

function remarkMarkdownDirectives() {
  return (tree: Root, file: VFile) => {
    visit(tree, (node, index, parent) => {
      if (
        !['containerDirective', 'leafDirective', 'textDirective'].includes(
          node.type,
        )
      ) {
        return;
      }
      if (
        node.type !== 'containerDirective' ||
        !['popup', 'details'].includes(node.name) ||
        node.children[0]?.type !== 'paragraph' ||
        !node.children[0]?.data?.directiveLabel
      ) {
        if (parent && index !== undefined) {
          parent.children[index] = {
            type: 'text',
            value: String(file.value).slice(
              node.position?.start.offset,
              node.position?.end.offset,
            ),
          };
        }
        return SKIP;
      }
      const label = toString(node.children.shift());
      node.data = {
        hName: 'div',
        hProperties: {
          dataMarkdownDirective: node.name,
          dataLabel: label,
        },
      };
    });
  };
}

function MarkdownDirective({
  type,
  label,
  children,
}: {
  type: string;
  label: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const { t } = useTranslation();
  const isDark = useTheme().palette.mode === 'dark';

  if (type === 'details') {
    return (
      <details>
        <summary>{label}</summary>
        {children}
      </details>
    );
  }
  return (
    <>
      <Button
        type="button"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        {label}
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        aria-labelledby={titleId}
        fullWidth
      >
        <DialogTitle id={titleId}>{label}</DialogTitle>
        <DialogContent>
          <div
            data-color-mode={isDark ? 'dark' : 'light'}
            className="wmde-markdown wmde-markdown-color"
            style={{ backgroundColor: 'transparent' }}
          >
            {children}
          </div>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>{t('close')}</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export const markdownDirectiveOptions: MarkdownOptions = {
  remarkPlugins: [remarkDirective, remarkMarkdownDirectives],
  components: {
    div: ({ node, children, ...props }) => {
      const type = node?.properties.dataMarkdownDirective;
      if (type === 'popup' || type === 'details') {
        return (
          <MarkdownDirective
            type={type}
            label={String(node?.properties.dataLabel ?? '')}
          >
            {children}
          </MarkdownDirective>
        );
      }
      return <div {...props}>{children}</div>;
    },
  },
};
