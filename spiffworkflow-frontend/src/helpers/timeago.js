/* eslint-disable no-restricted-syntax */
// https://gist.github.com/caiotarifa/30ae974f2293c761f3139dd194abd9e5
export const TimeAgo = (function awesomeFunc() {
  const self = {};

  // Public Methods
  self.locales = {
    prefix: '',
    sufix: 'atrás',

    seconds: 'alguns segundos atrás',
    minute: 'cerca de um minuto',
    minutes: '%d minutos',
    hour: 'cerca de uma hora',
    hours: 'cerca de %d horas',
    day: 'um dia',
    days: '%d dias',
    month: 'cerca de um mês',
    months: '%d meses',
    year: 'cerca de um ano',
    years: '%d anos',
  };

  self.inWords = function inWords(timeAgo) {
    const milliseconds = timeAgo * 1000;
    const seconds = Math.floor(
      (new Date() - parseInt(milliseconds, 10)) / 1000,
    );
    const separator = this.locales.separator || ' ';
    let words = this.locales.prefix + separator;
    let interval = 0;
    const intervals = {
      year: seconds / 31536000,
      month: seconds / 2592000,
      day: seconds / 86400,
      hour: seconds / 3600,
      minute: seconds / 60,
    };

    let distance = this.locales.seconds;

    // eslint-disable-next-line guard-for-in
    for (const key in intervals) {
      interval = Math.floor(intervals[key]);

      if (interval > 1) {
        distance = this.locales[`${key}s`];
        break;
      } else if (interval === 1) {
        distance = this.locales[key];
        break;
      }
    }

    distance = distance.replace(/%d/i, interval);
    words += distance + separator + this.locales.sufix;

    return words.trim();
  };

  return self;
})();
