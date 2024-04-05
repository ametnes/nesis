import { format, isValid } from 'date-fns';

export function formatDate(date) {
  if (date) {
    let parsedDate = new Date(date);
    if (isValid(parsedDate)) {
      return format(parsedDate, 'dd/MM/yyyy');
    }
  }
  return '';
}

export function formatDateTime(date) {
  if (date) {
    let parsedDate = new Date(date);
    if (isValid(parsedDate)) {
      return format(parsedDate, 'dd/MM/yyyy HH:mm:ss');
    }
  }
  return '';
}

export function formatNanosec(nanosec) {
  if (nanosec) {
    const millisec = nanosec / 1e6;
    let parsedDate = new Date(millisec);
    if (isValid(parsedDate)) {
      const splitsDate = parsedDate.toISOString().split('T');
      const formattedDate = `${splitsDate[0]} ${splitsDate[1].split('.')[0]}`;
      return formattedDate;
    }
  }
  return '';
}
