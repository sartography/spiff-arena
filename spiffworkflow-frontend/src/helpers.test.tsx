import { slugifyString } from './helpers';

test('it can slugify a string', () => {
  expect(slugifyString('hello---world_ and then Some such-')).toEqual(
    'hello-world-and-then-some-such'
  );
});
