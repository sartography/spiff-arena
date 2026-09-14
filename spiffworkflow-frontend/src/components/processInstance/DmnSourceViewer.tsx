import { useEffect, useRef, useState } from 'react';
import { Alert, Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
// @ts-expect-error dmn-js does not publish viewer declarations.
import Viewer from 'dmn-js/lib/Viewer';
import 'dmn-js/dist/assets/diagram-js.css';
import 'dmn-js/dist/assets/dmn-js-decision-table.css';
import 'dmn-js/dist/assets/dmn-js-drd.css';
import 'dmn-js/dist/assets/dmn-js-literal-expression.css';
import 'dmn-js/dist/assets/dmn-js-shared.css';
import 'dmn-js/dist/assets/dmn-font/css/dmn-embedded.css';

type DmnView = { type: string; element: { id: string; name?: string } };

export default function DmnSourceViewer({ xml }: { xml: string }) {
  const { t } = useTranslation();
  const container = useRef<HTMLDivElement>(null);
  const [views, setViews] = useState<DmnView[]>([]);
  const [selected, setSelected] = useState('');
  const [error, setError] = useState('');
  const viewerRef = useRef<InstanceType<typeof Viewer> | null>(null);

  useEffect(() => {
    let active = true;
    const viewer = new Viewer({ container: container.current });
    viewerRef.current = viewer;
    viewer.on(
      'views.changed',
      ({
        views: available,
        activeView,
      }: {
        views: DmnView[];
        activeView?: DmnView;
      }) => {
        if (active) {
          setViews(available);
          setSelected(activeView?.element.id || '');
        }
      },
    );
    setError('');
    setViews([]);
    viewer
      .importXML(xml)
      .then(async () => {
        if (!active) {
          return;
        }
        const available: DmnView[] = viewer.getViews();
        const initial =
          available.find((view) => view.type === 'decisionTable') ||
          available[0];
        if (initial) {
          await viewer.open(initial);
          if (active) {
            setViews(available);
            setSelected(initial.element.id);
          }
        }
      })
      .catch((exception: Error) => {
        if (active) {
          setError(exception.message);
        }
      });
    return () => {
      active = false;
      viewerRef.current = null;
      viewer.destroy();
    };
  }, [xml]);

  return (
    <>
      {error && <Alert severity="error">{error}</Alert>}
      {views.length > 1 && (
        <label>
          {t('decision_view')}{' '}
          <select
            value={selected}
            onChange={(event) => {
              const view = views.find(
                (item) => item.element.id === event.target.value,
              );
              if (view) {
                setSelected(view.element.id);
                viewerRef.current
                  ?.open(view)
                  .catch((exception: Error) => setError(exception.message));
              }
            }}
          >
            {views.map((view) => (
              <option key={view.element.id} value={view.element.id}>
                {view.element.name || view.element.id} ({view.type})
              </option>
            ))}
          </select>
        </label>
      )}
      <Box
        ref={container}
        sx={{ minHeight: 400, height: '60vh', overflow: 'auto', mt: 2 }}
      />
    </>
  );
}
