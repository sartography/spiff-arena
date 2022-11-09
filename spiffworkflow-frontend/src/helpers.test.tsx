import { convertSecondsToFormattedDate, slugifyString } from './helpers';

test('it can slugify a string', () => {
  expect(slugifyString('hello---world_ and then Some such-')).toEqual(
    'hello-world-and-then-some-such'
  );
});

test('it can keep the correct date when converting seconds to date', () => {
  const dateString = convertSecondsToFormattedDate(1666325400);
  expect(dateString).toEqual('2022-10-21');
});
