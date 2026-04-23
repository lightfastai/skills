const STATUS_RANK = {
  Pass: 0,
  Partial: 1,
  Fail: 2,
};

export function summarizeNumeric(values) {
  if (values.length === 0) {
    return {
      mean: 0,
      min: 0,
      max: 0,
    };
  }

  const total = values.reduce((sum, value) => sum + value, 0);
  return {
    mean: Math.round(total / values.length),
    min: Math.min(...values),
    max: Math.max(...values),
  };
}

export function worstStatus(statuses) {
  return statuses.reduce((worst, current) => {
    if (!worst) {
      return current;
    }
    return STATUS_RANK[current] > STATUS_RANK[worst] ? current : worst;
  }, null);
}

export function compareStatuses(left, right) {
  return STATUS_RANK[left] - STATUS_RANK[right];
}
