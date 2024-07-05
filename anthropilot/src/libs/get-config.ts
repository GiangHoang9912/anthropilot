import config = require('config')

export function getConfig(key: string, defaultValue: any = null) {
  const value = config.get(key)
  if (typeof value === 'undefined') {
    return defaultValue
  }
  return value
}
