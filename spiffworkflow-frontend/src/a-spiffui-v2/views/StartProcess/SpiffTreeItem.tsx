import { Typography } from '@mui/material';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import { useEffect, useState } from 'react';
import { Subject } from 'rxjs';

export default function SpiffTreeItem({
  group,
  model,
  stream,
}: {
  group: Record<string, any>;
  model: Record<string, any>;
  stream?: Subject<Record<string, any>>;
}) {
  const [crumbs, setCrumbs] = useState<string[]>([]);

  useEffect(() => {
    setCrumbs((prev) => {
      const arr = prev.concat(group.id);
      console.log(arr);
      return arr;
    });
  }, [group]);

  return (
    <>
      <Typography variant="caption">{JSON.stringify(crumbs)}</Typography>
      <TreeItem
        key={model.id}
        itemId={model.id}
        label={model.display_name}
        onClick={() => stream && stream.next(model)}
      />
    </>
  );
}
