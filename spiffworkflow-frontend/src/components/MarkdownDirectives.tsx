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
import type { Paragraph, Parents, Root, RootContent } from 'mdast';
import type { VFile } from 'vfile';

type MarkdownOptions = ComponentProps<typeof MDEditor.Markdown>;

// The helpers below are local replacements for `unist-util-visit`,
// `mdast-util-to-string`, and `remark-directive`. Inspired by those
// MIT-licensed packages, copyright (c) Titus Wormer <tituswormer@gmail.com>.
const SKIP = Symbol('skip');

function visit(
  node: Root | RootContent,
  callback: (
    child: RootContent,
    index: number,
    parent: Parents,
  ) => typeof SKIP | void,
): void {
  const children: RootContent[] =
    'children' in node ? (node.children as RootContent[]) : [];
  children.forEach((child, index) => {
    if (callback(child, index, node as Parents) !== SKIP) {
      visit(child, callback);
    }
  });
}

function mdastToPlainText(node: RootContent | undefined): string {
  if (!node) {
    return '';
  }
  if (
    node.type === 'text' ||
    node.type === 'inlineCode' ||
    node.type === 'code'
  ) {
    return node.value;
  }
  if (node.type === 'break') {
    return '\n';
  }
  if (node.type === 'image' || node.type === 'imageReference') {
    return node.alt ?? '';
  }
  const children = 'children' in node ? (node.children as RootContent[]) : [];
  return children.map(mdastToPlainText).join('');
}

const DIRECTIVE_NAMES = ['popup', 'details'];
const OPENER_PATTERN = /^:::(\w+)\[([^\]]*)\]\n?/;
const CLOSING_PATTERN = /\n?:::$/;

function getDirectiveOpener(
  node: RootContent,
): { name: string; label: string } | null {
  if (node.type !== 'paragraph' || node.children.length === 0) {
    return null;
  }
  const first = node.children[0];
  if (first.type !== 'text') {
    return null;
  }
  const match = OPENER_PATTERN.exec(first.value);
  if (!match || !DIRECTIVE_NAMES.includes(match[1])) {
    return null;
  }
  return { name: match[1], label: match[2] };
}

function stripOpener(paragraph: Paragraph): void {
  const first = paragraph.children[0];
  if (first.type !== 'text') {
    return;
  }
  const match = OPENER_PATTERN.exec(first.value);
  if (match) {
    first.value = first.value.slice(match[0].length);
  }
}

function endsWithClosingMarker(node: RootContent): boolean {
  const children = 'children' in node ? node.children : undefined;
  if (!children || children.length === 0) {
    return node.type === 'text' && CLOSING_PATTERN.test(node.value);
  }
  return endsWithClosingMarker(children[children.length - 1] as RootContent);
}

function stripClosingMarker(node: RootContent): void {
  const children = 'children' in node ? node.children : undefined;
  if (!children || children.length === 0) {
    if (node.type === 'text') {
      const match = CLOSING_PATTERN.exec(node.value);
      if (match) {
        node.value = node.value.slice(0, match.index);
      }
    }
    return;
  }
  stripClosingMarker(children[children.length - 1] as RootContent);
}

function paragraphHasContent(paragraph: Paragraph): boolean {
  return paragraph.children.some(
    (child) => child.type !== 'text' || child.value.trim() !== '',
  );
}

/**
 * Parses `:::popup[Label]` and `:::details[Label]` blocks into directive nodes
 * so that the Markdown pipeline can render them without `remark-directive`.
 *
 * Inspired by remark-directive (MIT, Titus Wormer).
 */
function remarkMarkdownDirectiveSyntax() {
  return (tree: Root) => {
    for (let index = 0; index < tree.children.length; index += 1) {
      const opener = getDirectiveOpener(tree.children[index]);
      if (!opener) {
        continue;
      }
      const openingParagraph = tree.children[index] as Paragraph;
      let closingIndex = -1;
      if (endsWithClosingMarker(openingParagraph)) {
        closingIndex = index;
      } else {
        for (let next = index + 1; next < tree.children.length; next += 1) {
          if (endsWithClosingMarker(tree.children[next])) {
            closingIndex = next;
            break;
          }
        }
      }
      if (closingIndex === -1) {
        continue;
      }
      stripOpener(openingParagraph);
      if (closingIndex === index) {
        stripClosingMarker(openingParagraph);
      }
      const content: RootContent[] = tree.children.slice(
        index + 1,
        closingIndex + 1,
      );
      if (closingIndex > index) {
        stripClosingMarker(tree.children[closingIndex]);
        const closingNode = tree.children[closingIndex];
        if (
          closingNode.type === 'paragraph' &&
          !paragraphHasContent(closingNode)
        ) {
          content.pop();
        }
      }
      const children: RootContent[] = [
        {
          type: 'paragraph',
          data: { directiveLabel: true },
          children: [{ type: 'text', value: opener.label }],
        },
      ];
      if (paragraphHasContent(openingParagraph)) {
        children.push(openingParagraph);
      }
      children.push(...content);
      tree.children.splice(index, closingIndex - index + 1, {
        type: 'containerDirective',
        name: opener.name,
        children,
      } as unknown as RootContent);
    }
  };
}

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
      const label = mdastToPlainText(node.children.shift());
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
  remarkPlugins: [remarkMarkdownDirectiveSyntax, remarkMarkdownDirectives],
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
