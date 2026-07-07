export const PROCESS_DESCRIPTION_LIMIT = 240;

export const truncateProcessDescription = (
  description?: string | null,
  limit = PROCESS_DESCRIPTION_LIMIT,
) => {
  if (!description) {
    return '';
  }

  const trimmedDescription = description.trim();

  if (trimmedDescription.length <= limit) {
    return trimmedDescription;
  }

  return `${trimmedDescription.slice(0, limit).trimEnd()}...`;
};

export const processDescriptionSx = {
  overflowWrap: 'anywhere',
  wordBreak: 'break-word',
  whiteSpace: 'normal',
};
