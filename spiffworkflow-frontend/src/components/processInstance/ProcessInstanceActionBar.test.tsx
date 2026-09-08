import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ProcessInstance } from '../../interfaces';
import ProcessInstanceActionBar from './ProcessInstanceActionBar';

vi.mock('react-i18next', () => {
  return {
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

vi.mock('../ConfirmIconButton', () => {
  return {
    default: ({ iconDescription, onConfirmation, ...props }: any) => (
      <button
        type="button"
        aria-label={iconDescription}
        onClick={onConfirmation}
        data-testid={props['data-testid']}
      >
        {iconDescription}
      </button>
    ),
  };
});

const baseProps = {
  copiedShortLinkToClipboard: false,
  onCopyShortLink: vi.fn(),
  onCopiedNotificationClose: vi.fn(),
  onDelete: vi.fn(),
  onMigrate: vi.fn(),
  onResume: vi.fn(),
  onSuspend: vi.fn(),
  onTerminate: vi.fn(),
};

const testInstance = (status: string) =>
  ({
    id: 42,
    status,
  }) as ProcessInstance;

const fullPermissions = {
  canDelete: true,
  canMigrate: true,
  canResume: true,
  canSuspend: true,
  canTerminate: true,
};

describe('ProcessInstanceActionBar', () => {
  it('shows terminate and suspend actions for a running instance', () => {
    render(
      <ProcessInstanceActionBar
        processInstance={testInstance('waiting')}
        {...fullPermissions}
        {...baseProps}
      />,
    );
    expect(screen.getByLabelText('terminate_button')).toBeInTheDocument();
    expect(screen.getByLabelText('suspend_tooltip')).toBeInTheDocument();
    expect(
      screen.queryByTestId('process-instance-delete'),
    ).not.toBeInTheDocument();
  });

  it('shows migrate, resume, and delete actions for a suspended instance', () => {
    render(
      <ProcessInstanceActionBar
        processInstance={testInstance('suspended')}
        {...fullPermissions}
        {...baseProps}
      />,
    );
    expect(screen.getByLabelText('migrate')).toBeInTheDocument();
    expect(screen.getByLabelText('resume')).toBeInTheDocument();
    expect(
      screen.queryByTestId('process-instance-delete'),
    ).not.toBeInTheDocument();
  });

  it('shows only the delete action for a terminal instance', () => {
    render(
      <ProcessInstanceActionBar
        processInstance={testInstance('complete')}
        {...fullPermissions}
        {...baseProps}
      />,
    );
    expect(screen.getByTestId('process-instance-delete')).toBeInTheDocument();
    expect(screen.queryByLabelText('terminate_button')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('suspend_tooltip')).not.toBeInTheDocument();
  });

  it('copies the short link and shows a confirmation toast', () => {
    const onCopyShortLink = vi.fn();
    const onCopiedNotificationClose = vi.fn();
    render(
      <ProcessInstanceActionBar
        processInstance={testInstance('waiting')}
        {...fullPermissions}
        {...baseProps}
        onCopyShortLink={onCopyShortLink}
        copiedShortLinkToClipboard
        onCopiedNotificationClose={onCopiedNotificationClose}
      />,
    );
    fireEvent.click(screen.getByLabelText('copy_shareable_link_tooltip'));
    expect(onCopyShortLink).toHaveBeenCalledTimes(1);
    expect(screen.getByText('copied_link_to_clipboard')).toBeInTheDocument();
  });
});
