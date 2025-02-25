import { Typography, Card, CardActionArea, CardContent } from '@mui/material';
import { DataStore } from '../../interfaces';

const defaultStyle = {
  borderRadius: 2,
  padding: 2,
  margin: 2,
  borderWidth: 1,
  borderStyle: 'solid',
  borderColor: 'borders.primary',
  minWidth: 320,
  position: 'relative',
  ':hover': {
    backgroundColor: 'background.bluegreylight',
  },
};

export default function DataStoreCard({ dataStore }: { dataStore: DataStore }) {
  return (
    <Card sx={defaultStyle}>
      <CardActionArea
        href={`/newui/data-stores/${dataStore.id}/edit?type=${dataStore.type}&parentGroupId=${dataStore.location}`}
      >
        <CardContent>
          <Typography variant="body2" sx={{ fontWeight: 700 }}>
            {dataStore.name}
          </Typography>
          <Typography
            variant="caption"
            sx={{ fontWeight: 700, color: 'text.secondary' }}
          >
            {dataStore.description || '--'}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
