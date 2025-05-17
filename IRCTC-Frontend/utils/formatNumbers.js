
export function formatNumber(number) {

    const absoluteValue = Math.abs(number);
  
    if (absoluteValue >= 10000000) {
      return `${(absoluteValue / 10000000).toFixed(1)} Cr`;
    } else if (absoluteValue >= 100000) {
      return `${(absoluteValue / 100000).toFixed(1)} L`;
    } else if (absoluteValue >= 1000) {
      return `${(absoluteValue / 1000).toFixed(1)} K`;
    } else {
      return `${absoluteValue}`;
    }
  }
  