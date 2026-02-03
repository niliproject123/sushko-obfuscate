import { useCallback } from 'react';

type SetError = (error: string | null) => void;

/**
 * Creates an async callback wrapper that handles errors consistently.
 * Clears error before execution, captures and formats errors on failure.
 */
export function createAsyncAction<TArgs extends unknown[], TResult>(
  setError: SetError,
  action: (...args: TArgs) => Promise<TResult>,
  errorMessage: string
): (...args: TArgs) => Promise<TResult> {
  return async (...args: TArgs): Promise<TResult> => {
    setError(null);
    try {
      return await action(...args);
    } catch (err) {
      const message = err instanceof Error ? err.message : errorMessage;
      setError(message);
      throw err;
    }
  };
}

/**
 * Hook that creates a memoized async action with error handling.
 */
export function useAsyncAction<TArgs extends unknown[], TResult>(
  setError: SetError,
  action: (...args: TArgs) => Promise<TResult>,
  errorMessage: string,
  deps: React.DependencyList = []
): (...args: TArgs) => Promise<TResult> {
  return useCallback(
    createAsyncAction(setError, action, errorMessage),
    [setError, errorMessage, ...deps]
  );
}
