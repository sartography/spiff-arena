import { useEffect, useMemo, useState } from 'react';
import useProcessGroups from '../../hooks/useProcessGroups';
import HttpService from '../../services/HttpService';
import { ProcessModelStatsMap } from '../../interfaces';
import {
  buildGroupInstanceCountMap,
  GroupInstanceCountMap,
} from './groupTreeHelpers';

/**
 * Data layer for the collapsible process-group views. Loads the full recursive
 * process-group tree (one call) and the per-model instance stats (one call),
 * and derives exact per-group instance counts client-side. No backend changes.
 */
export default function useProcessGroupTree() {
  const { processGroups, loading } = useProcessGroups({ processInfo: {} });
  const [stats, setStats] = useState<ProcessModelStatsMap>({});

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: '/process-models/stats',
      successCallback: (result: ProcessModelStatsMap) => setStats(result),
      onUnauthorized: () => setStats({}),
    });
  }, []);

  const groupInstanceCountMap = useMemo<GroupInstanceCountMap>(
    () => buildGroupInstanceCountMap(stats),
    [stats],
  );

  const groupInstanceCount = (groupId: string): number =>
    groupInstanceCountMap[groupId] ?? 0;
  const modelInstanceCount = (modelId: string): number =>
    stats[modelId]?.instance_count ?? 0;

  return {
    processGroups,
    loading,
    stats,
    groupInstanceCountMap,
    groupInstanceCount,
    modelInstanceCount,
  };
}
