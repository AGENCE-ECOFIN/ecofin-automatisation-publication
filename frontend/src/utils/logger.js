/**
 * Logs structurés : en production, seules les erreurs sont utiles ;
 * en développement, tout passe en console avec un préfixe lisible.
 */
const PREFIX = '[publication]';

const enabled = process.env.NODE_ENV === 'development';

function format(scope, message, data) {
  if (data !== undefined) {
    return [`${PREFIX} ${scope}`, message, data];
  }
  return [`${PREFIX} ${scope}`, message];
}

export const log = {
  debug(scope, message, data) {
    if (!enabled) return;
    console.debug(...format(scope, message, data));
  },
  info(scope, message, data) {
    if (!enabled) return;
    console.info(...format(scope, message, data));
  },
  warn(scope, message, data) {
    console.warn(...format(scope, message, data));
  },
  error(scope, message, data) {
    console.error(...format(scope, message, data));
  },
};
