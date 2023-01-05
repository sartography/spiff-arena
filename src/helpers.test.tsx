import {
  convertSecondsToFormattedDateString,
  isInteger,
  slugifyString,
  underscorizeString,
} from './helpers';

test('it can slugify a string', () => {
  expect(slugifyString('hello---world_ and then Some such-')).toEqual(
    'hello-world-and-then-some-such'
  );
});

test('it can underscorize a string', () => {
  expect(underscorizeString('hello---world_ and then Some such-')).toEqual(
    'hello_world_and_then_some_such'
  );
});

test('it can keep the correct date when converting seconds to date', () => {
  const dateString = convertSecondsToFormattedDateString(1666325400);
  expect(dateString).toEqual('2022-10-21');
});

test('it can validate numeric values', () => {
  expect(isInteger('11')).toEqual(true);
  expect(isInteger('hey')).toEqual(false);
  expect(isInteger('        ')).toEqual(false);
  expect(isInteger('1 2')).toEqual(false);
  expect(isInteger(2)).toEqual(true);
});
