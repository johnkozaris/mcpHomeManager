import { useState, useEffect } from "react";

/**
 * Returns a debounced copy of `value` that only updates after the
 * caller has stopped changing it for `delay` milliseconds.
 */
export function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);

  return debounced;
}
