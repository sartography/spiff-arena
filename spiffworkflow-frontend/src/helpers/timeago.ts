import i18n from '../i18n';

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
  const getLocales: () => Locales = () => ({
    prefix: i18n.t('time_ago_prefix'),
    sufix: i18n.t('time_ago_suffix'),
    seconds: i18n.t('time_less_than_minute'),
    minute: i18n.t('time_about_minute'),
    minutes: i18n.t('time_minutes'),
    hour: i18n.t('time_about_hour'),
    hours: i18n.t('time_about_hours'),
    day: i18n.t('time_day'),
    days: i18n.t('time_days'),
    month: i18n.t('time_about_month'),
    months: i18n.t('time_months'),
    year: i18n.t('time_about_year'),
    years: i18n.t('time_years'),
  });

  function inWords(timeAgo: number): string {
    const locales = getLocales();
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

  return { getLocales, inWords };
})();
