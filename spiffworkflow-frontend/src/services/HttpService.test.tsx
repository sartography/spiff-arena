import HttpService from './HttpService';

test('it can use given http status message in messageForHttpError', () => {
  expect(HttpService.messageForHttpError(400, 'Bad Request')).toEqual(
    'HTTP Error 400: Bad Request',
  );
});

test('it can figure out http status message if not given in messageForHttpError', () => {
  expect(HttpService.messageForHttpError(400, '')).toEqual(
    'HTTP Error 400: Bad Request',
  );
});
