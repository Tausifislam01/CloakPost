export function isLoggedIn(): boolean {
  return document.cookie.includes('sessionid=')
}
