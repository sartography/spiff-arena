import {
  Typography,
  Card,
  CardActionArea,
  CardContent,
  Stack,
} from '@mui/material';
import { DataStore } from '../interfaces';

const defaultStyle = {
  ':hover': {
    backgroundColor: 'background.bluegreylight',
  },
  padding: 2,
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  position: 'relative',
  border: '1px solid',
  borderColor: 'borders.primary',
  borderRadius: 2,
};

export default function DataStoreCard({ dataStore }: { dataStore: DataStore }) {
  return (
    <Card elevation={0} sx={defaultStyle}>
      <CardActionArea
        href={`/data-stores/${dataStore.id}/edit?type=${dataStore.type}&parentGroupId=${dataStore.location}`}
      >
        <CardContent>
          <Stack>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              {dataStore.name}
            </Typography>
            <Typography
              variant="caption"
              sx={{ fontWeight: 700, color: 'text.secondary' }}
            >
              {dataStore.description || '--'}
            </Typography>
          </Stack>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
