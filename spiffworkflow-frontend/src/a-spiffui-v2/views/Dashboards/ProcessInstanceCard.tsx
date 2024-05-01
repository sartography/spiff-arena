import { Stack } from '@mui/material';
import { useEffect } from 'react';

export default function ProcessInstanceCard({
  instance,
}: {
  instance: Record<string, any>;
}) {
  useEffect(() => {
    console.log(instance);
  }, []);
  return <Stack>{instance.status}</Stack>;
}
