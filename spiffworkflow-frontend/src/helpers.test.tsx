import {
  buildUniqueMilestoneNamesPath,
  isANumber,
  mergeSelectedStringOption,
  slugifyString,
  underscorizeString,
  recursivelyChangeNullAndUndefined,
  isURL,
} from './helpers';

test('it can slugify a string', () => {
  expect(slugifyString('hello---world_ and then Some such-')).toEqual(
    'hello-world-and-then-some-such',
  );
});

test('it can underscorize a string', () => {
  expect(underscorizeString('hello---world_ and then Some such-')).toEqual(
    'hello_world_and_then_some_such',
  );
});

test('it can validate numeric values', () => {
  expect(isANumber('11')).toEqual(true);
  expect(isANumber('hey')).toEqual(false);
  expect(isANumber('        ')).toEqual(false);
  expect(isANumber('1 2')).toEqual(false);
  expect(isANumber(2)).toEqual(true);
  expect(isANumber(2.0)).toEqual(true);
  expect(isANumber('2.0')).toEqual(true);
});

test('it can replace undefined values in object with null', () => {
  const sampleData = {
    talentType: 'foo',
    rating: 'bar',
    contacts: {
      gmeets: undefined,
      zoom: undefined,
      phone: 'baz',
      awesome: false,
      info: '',
    },
    items: [
      undefined,
      {
        contacts: {
          gmeets: undefined,
          zoom: undefined,
          phone: 'baz',
        },
      },
      'HEY',
    ],
    undefined,
  };

  expect((sampleData.items[1] as any).contacts.zoom).toEqual(undefined);

  const result = recursivelyChangeNullAndUndefined(sampleData, null);
  expect(result).toEqual(sampleData);
  expect(result.items[1].contacts.zoom).toEqual(null);
  expect(result.items[2]).toEqual('HEY');
  expect(result.contacts.awesome).toEqual(false);
  expect(result.contacts.info).toEqual('');
});

test('it can replace null values in object with undefined', () => {
  const sampleData = {
    talentType: 'foo',
    rating: 'bar',
    contacts: {
      gmeets: null,
      zoom: null,
      phone: 'baz',
      awesome: false,
      info: '',
    },
    items: [
      null,
      {
        contacts: {
          gmeets: null,
          zoom: null,
          phone: 'baz',
        },
      },
      'HEY',
    ],
  };

  expect((sampleData.items[1] as any).contacts.zoom).toEqual(null);

  const result = recursivelyChangeNullAndUndefined(sampleData, undefined);
  expect(result).toEqual(sampleData);
  expect(result.items[1].contacts.zoom).toEqual(undefined);
  expect(result.items[2]).toEqual('HEY');
  expect(result.contacts.awesome).toEqual(false);
  expect(result.contacts.info).toEqual('');
});

test('it can identify urls', () => {
  const urls = [
    'http://localhost:7001/public/tasks/94/61efeb05-7278-4de8-979d-b4580cfc0233',
    'http://localhost/public/tasks/94/61efeb05-7278-4de8-979d-b4580cfc0233',
    'https://www.google.com',
  ];
  urls.forEach((url: string) => {
    const result = isURL(url);
    expect(result).toBe(true);
  });
  const badUrls = [
    'localhost:7001/public/tasks/94/61efeb05-7278-4de8-979d-b4580cfc0233',
    'localhost/public/tasks/94/61efeb05-7278-4de8-979d-b4580cfc0233',
    'www.google.com',
  ];
  badUrls.forEach((url: string) => {
    const result = isURL(url);
    expect(result).toBe(false);
  });
});

test('it builds milestone names path for scoped process instance views', () => {
  expect(
    buildUniqueMilestoneNamesPath({
      variant: 'for-me',
      withRelationToMe: false,
      processModelIdentifier: null,
    }),
  ).toEqual('/process-instances/unique-milestone-names?with_relation_to_me=true');

  expect(
    buildUniqueMilestoneNamesPath({
      variant: 'all',
      withRelationToMe: true,
      processModelIdentifier: 'group/sample',
    }),
  ).toEqual(
    '/process-instances/unique-milestone-names?with_relation_to_me=true&process_model_identifier=group%2Fsample',
  );

  expect(
    buildUniqueMilestoneNamesPath({
      variant: 'all',
      withRelationToMe: false,
      processModelIdentifier: 'group/sample',
    }),
  ).toEqual(
    '/process-instances/unique-milestone-names?process_model_identifier=group%2Fsample',
  );
});

test('it preserves the selected milestone in the available options', () => {
  expect(
    mergeSelectedStringOption(['Milestone A', 'Milestone B'], null),
  ).toEqual(['Milestone A', 'Milestone B']);

  expect(
    mergeSelectedStringOption(['Milestone A', 'Milestone B'], 'Milestone B'),
  ).toEqual(['Milestone A', 'Milestone B']);

  expect(
    mergeSelectedStringOption(['Milestone A', 'Milestone B'], 'Milestone C'),
  ).toEqual(['Milestone C', 'Milestone A', 'Milestone B']);
});
