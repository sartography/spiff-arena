import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import MDEditor from '@uiw/react-md-editor';
import { createTheme, ThemeProvider } from '@mui/material';
import MarkdownRenderer from './MarkdownRenderer';
import { markdownDirectiveOptions } from './MarkdownDirectives';

const popup = ':::popup[Why we ask]\nA **helpful** explanation.\n:::';

it('opens a named popup, closes with Escape, and restores focus to its trigger', async () => {
  render(<MarkdownRenderer source={`Before\n\n${popup}\n\nAfter`} />);
  expect(screen.getByText('Before')).toBeVisible();
  expect(screen.getByText('After')).toBeVisible();
  expect(
    screen.queryByText('explanation.', { exact: false }),
  ).not.toBeInTheDocument();

  const trigger = screen.getByRole('button', { name: 'Why we ask' });
  trigger.focus();
  fireEvent.click(trigger);
  const dialog = screen.getByRole('dialog', { name: 'Why we ask' });
  expect(within(dialog).getByText('helpful').tagName).toBe('STRONG');
  fireEvent.keyDown(dialog, { key: 'Escape' });
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
  expect(trigger).toHaveFocus();
});

it('keeps multiple popups independent and supports the Close button', async () => {
  render(
    <MarkdownRenderer
      source={`${popup}\n\n:::popup[More information]\nOther content\n:::`}
    />,
  );
  fireEvent.click(screen.getByRole('button', { name: 'More information' }));
  expect(
    screen.getByRole('dialog', { name: 'More information' }),
  ).toHaveTextContent('Other content');
  expect(screen.queryByText('helpful')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Close' }));
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
});

it('renders details collapsed with formatted Markdown inside', () => {
  const { container } = render(
    <MarkdownRenderer
      source={
        ':::details[What to include]\n- Your **title**\n- [Help](https://example.com)\n:::'
      }
    />,
  );
  const details = container.querySelector('details');
  expect(details).not.toHaveAttribute('open');
  expect(details?.querySelector('summary')).toHaveTextContent(
    'What to include',
  );
  expect(details?.querySelectorAll('li')).toHaveLength(2);
  expect(details?.querySelector('strong')).toHaveTextContent('title');
  expect(details?.querySelector('a')).toHaveAttribute(
    'href',
    'https://example.com',
  );
});

it('leaves inline code, fenced examples, unknown directives, and unlabeled directives literal', () => {
  const source = `\`${popup.split('\n')[0]}\`\n\n\`\`\`markdown\n${popup}\n\`\`\`\n\n:::other[Example]\nBody\n:::\n\n:::popup\nNo label\n:::`;
  const { container } = render(<MarkdownRenderer source={source} />);
  expect(container.querySelector('pre code')).toHaveTextContent(
    ':::popup[Why we ask]',
  );
  expect(container).toHaveTextContent(':::other[Example]');
  expect(container).toHaveTextContent(':::popup No label :::');
  expect(
    screen.queryByRole('button', { name: 'Why we ask' }),
  ).not.toBeInTheDocument();
});

it('preserves normal Markdown, tables, and Spiff formatting', () => {
  const source =
    '# Heading\n\n**Label**: value\n\n| Name | Value |\n| --- | --- |\n| Example | 1 |\n\nSPIFF_FORMAT:::convert_seconds_to_duration_for_display(60)';
  render(<MarkdownRenderer source={source} />);
  expect(screen.getByRole('heading', { name: 'Heading' })).toBeVisible();
  expect(screen.getByText('Label').tagName).toBe('STRONG');
  expect(screen.getByRole('table')).toHaveTextContent('Example');
  expect(screen.queryByText(/SPIFF_FORMAT/)).not.toBeInTheDocument();
});

it('uses the same directives in editor previews and preserves dark mode in the dialog', () => {
  render(
    <ThemeProvider theme={createTheme({ palette: { mode: 'dark' } })}>
      <MDEditor.Markdown {...markdownDirectiveOptions} source={popup} />
    </ThemeProvider>,
  );
  fireEvent.click(screen.getByRole('button', { name: 'Why we ask' }));
  expect(
    screen.getByText('helpful').closest('[data-color-mode]'),
  ).toHaveAttribute('data-color-mode', 'dark');
});
