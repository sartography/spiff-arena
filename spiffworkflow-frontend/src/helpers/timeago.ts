/* eslint-disable no-restricted-syntax */
// https://gist.github.com/caiotarifa/30ae974f2293c761f3139dd194abd9e5
type Locales = {
  prefix: string;
  sufix: string;
  seconds: string;
  minute: string;
  minutes: string;
  hour: string;
  hours: string;
  day: string;
  days: string;
  month: string;
  months: string;
  year: string;
  years: string;
  separator?: string;
};

export const TimeAgo = (function awesomeFunc() {
  const locales: Locales = {
    prefix: '',
    sufix: 'ago',

    seconds: 'less than a minute',
    minute: 'about a minute',
    minutes: '%d minutes',
    hour: 'about an hour',
    hours: 'about %d hours',
    day: 'a day',
    days: '%d days',
    month: 'about a month',
    months: '%d months',
    year: 'about a year',
    years: '%d years',
  };

  function inWords(timeAgo: number): string {
    const milliseconds = timeAgo * 1000;
    const seconds = Math.floor(
      (new Date().getTime() - parseInt(milliseconds.toString(), 10)) / 1000,
    );
    const separator = locales.separator || ' ';
    let words = locales.prefix + separator;
    let interval = 0;
    const intervals: Record<string, number> = {
      year: seconds / 31536000,
      month: seconds / 2592000,
      day: seconds / 86400,
      hour: seconds / 3600,
      minute: seconds / 60,
    };

    let distance: any = null;
    Object.keys(intervals).forEach((key: string) => {
      if (distance !== null) {
        return;
      }
      interval = Math.floor(intervals[key]);

      if (interval > 1) {
        distance = locales[`${key}s` as keyof Locales];
      }
      if (interval === 1) {
        distance = locales[key as keyof Locales];
      }
    });
    if (distance === null) {
      distance = locales.seconds;
    }

    distance = distance.replace(/%d/i, interval.toString());
    words += distance + separator + locales.sufix;

    return words.trim();
  }

  return { locales, inWords };
})();
