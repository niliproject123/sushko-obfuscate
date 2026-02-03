/**
 * Check if the app is running locally (desktop exe or dev server).
 */
export function isLocal(): boolean {
  return /^(127\.|localhost)/.test(window.location.hostname);
}
