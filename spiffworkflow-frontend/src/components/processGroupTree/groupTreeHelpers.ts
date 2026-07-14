import {
  ProcessGroup,
  ProcessModel,
  ProcessModelStatsMap,
} from '../../interfaces';

export type GroupInstanceCountMap = Record<string, number>;

/**
 * Build a map of process-group id -> total instance count, derived purely from
 * the /process-models/stats response. A model id encodes its full group path
 * (e.g. "r2r/r2r-level-4-maps/mje-process"), so every ancestor group prefix
 * accumulates the model's instance_count. This gives exact per-group counts
 * with no extra backend calls (the backend has no group-by/aggregation).
 */
export function buildGroupInstanceCountMap(
  stats: ProcessModelStatsMap,
): GroupInstanceCountMap {
  const map: GroupInstanceCountMap = {};
  Object.entries(stats).forEach(([modelId, stat]) => {
    const count = stat?.instance_count ?? 0;
    if (!count) {
      return;
    }
    const parts = modelId.split('/');
    // Every prefix BEFORE the final (model) segment is an ancestor group.
    for (let i = 1; i < parts.length; i += 1) {
      const groupId = parts.slice(0, i).join('/');
      map[groupId] = (map[groupId] ?? 0) + count;
    }
  });
  return map;
}

/** Total number of process models nested anywhere under a group. */
export function buildGroupModelCountMap(
  groups: ProcessGroup[],
): Record<string, number> {
  const map: Record<string, number> = {};
  const walk = (group: ProcessGroup): number => {
    let total = group.process_models?.length ?? 0;
    (group.process_groups ?? []).forEach((child) => {
      total += walk(child);
    });
    map[group.id] = total;
    return total;
  };
  groups.forEach(walk);
  return map;
}

function searchLabelFor(item: { display_name?: string; id: string }): string {
  return `${item.display_name ?? ''} ${item.id}`.toLowerCase();
}

/**
 * Prune a process-group tree to nodes matching a free-text search. A group that
 * matches itself keeps all of its descendants; otherwise only matching child
 * groups/models are retained. Returns a new tree (no mutation).
 */
export function filterProcessGroupTree(
  groups: ProcessGroup[],
  term: string,
): ProcessGroup[] {
  const trimmed = term.trim().toLowerCase();
  if (!trimmed) {
    return groups;
  }
  const tokens = trimmed.split(/\s+/);
  const matches = (label: string): boolean =>
    tokens.every((token) => label.includes(token));

  const walk = (group: ProcessGroup): ProcessGroup | null => {
    const groupMatches = matches(searchLabelFor(group));
    if (groupMatches) {
      return group;
    }
    const childGroups = (group.process_groups ?? [])
      .map(walk)
      .filter((child): child is ProcessGroup => child !== null);
    const childModels = (group.process_models ?? []).filter(
      (model: ProcessModel) => matches(searchLabelFor(model)),
    );
    if (childGroups.length > 0 || childModels.length > 0) {
      return {
        ...group,
        process_groups: childGroups,
        process_models: childModels,
      };
    }
    return null;
  };

  return groups
    .map(walk)
    .filter((group): group is ProcessGroup => group !== null);
}
