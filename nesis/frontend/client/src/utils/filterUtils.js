export function filterItems(items, filterValues, customFilterFn) {
  if (!items) {
    return [];
  }
  return items.filter((item) => {
    let matches = true;
    Object.entries(filterValues).forEach(([fieldKey, value]) => {
      let itemValueAsString = `${item[fieldKey]}`.toLowerCase();
      if (value && !itemValueAsString.includes(`${value}`.toLowerCase())) {
        matches = false;
      }
    });
    if (customFilterFn && !customFilterFn(item)) {
      matches = false;
    }
    return matches;
  });
}
