import {
  Card,
  CardActionArea,
  CardContent,
  Stack,
  Typography,
} from '@mui/material';
import { useNavigate } from 'react-router';
import { Subject } from 'rxjs';

/**
 * Displays the Process Group info.
 * Note that Groups and Models may seem similar, but
 * some of the event handling and stream info is different.
 * Eventually might refactor to a common component, but at this time
 * it's useful to keep them separate.
 */
export default function ProcessGroupCard({
  group,
  stream,
  navigateToPage = false,
}: {
  group: Record<string, any>;
  stream?: Subject<Record<string, any>>;
  navigateToPage?: boolean;
}) {
  const navigate = useNavigate();
  const captionColor = 'text.secondary';

  return (
    <Card
      elevation={0}
      sx={{
        padding: 2,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        position: 'relative',
        border: '1px solid',
        borderColor: 'borders.primary',
        borderRadius: 2,
        ':hover': {
          backgroundColor: 'background.bluegreylight',
        },
      }}
      onClick={() => {
        if (stream) {
          stream.next(group);
        }
        if (navigateToPage) {
          navigate(`/process-groups/${group.id.replaceAll('/', ':')}`);
        }
      }}
    >
      <CardActionArea>
        <CardContent>
          <Stack>
            <Typography variant="body1" sx={{ fontWeight: 700 }}>
              {group.display_name}
            </Typography>

            <Typography
              variant="caption"
              sx={{ fontWeight: 700, color: 'text.secondary' }}
            >
              {group.description || '--'}
            </Typography>

            <Typography variant="caption" sx={{ color: captionColor }}>
              Groups: {group.process_groups.length}
            </Typography>
            <Typography variant="caption" sx={{ color: captionColor }}>
              Models: {group.process_models.length}
            </Typography>
          </Stack>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
