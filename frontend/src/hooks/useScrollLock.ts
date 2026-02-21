import { useEffect } from "react";

/**
 * Locks body scrolling while a modal/overlay is open.
 * Ref-counted: multiple concurrent locks are safe — scroll is restored
 * only when the last lock is released.
 */
let lockCount = 0;

export function useScrollLock(locked: boolean): void {
  useEffect(() => {
    if (!locked) return;

    if (lockCount === 0) {
      document.body.style.overflow = "hidden";
    }
    lockCount++;

    return () => {
      lockCount--;
      if (lockCount === 0) {
        document.body.style.overflow = "";
      }
    };
  }, [locked]);
}
