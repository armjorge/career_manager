import {
  AuthenticationDetails,
  CognitoAccessToken,
  CognitoIdToken,
  CognitoRefreshToken,
  CognitoUser,
  CognitoUserAttribute,
  CognitoUserPool,
  CognitoUserSession,
} from 'amazon-cognito-identity-js'

import {
  cognitoHostedUiBaseUrl,
  env,
  isCognitoConfigured,
  isHostedUiConfigured,
  oauthRedirectUri,
} from '../config/env'
import {
  buildAuthorizeUrl,
  clearPkceSession,
  exchangeAuthorizationCode,
} from './oauth'

export type AuthUser = {
  email: string
  sub: string
}

function getUserPool(): CognitoUserPool {
  if (!isCognitoConfigured()) {
    throw new Error(
      'Cognito is not configured. Set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_USER_POOL_CLIENT_ID.',
    )
  }

  return new CognitoUserPool({
    UserPoolId: env.cognitoUserPoolId,
    ClientId: env.cognitoClientId,
  })
}

function getCognitoUser(email: string): CognitoUser {
  return new CognitoUser({
    Username: email,
    Pool: getUserPool(),
  })
}

export function getCurrentSession(): Promise<CognitoUserSession | null> {
  if (!isCognitoConfigured()) return Promise.resolve(null)

  const user = getUserPool().getCurrentUser()
  if (!user) return Promise.resolve(null)

  return new Promise((resolve, reject) => {
    user.getSession((err: Error | null, session: CognitoUserSession | null) => {
      if (err) {
        reject(err)
        return
      }
      resolve(session?.isValid() ? session : null)
    })
  })
}

export async function getIdToken(): Promise<string | null> {
  const session = await getCurrentSession()
  return session?.getIdToken().getJwtToken() ?? null
}

export function signUp(email: string, password: string): Promise<void> {
  const attributeList = [
    new CognitoUserAttribute({ Name: 'email', Value: email }),
  ]

  return new Promise((resolve, reject) => {
    getUserPool().signUp(email, password, attributeList, [], (err) => {
      if (err) {
        reject(err)
        return
      }
      resolve()
    })
  })
}

export function confirmSignUp(email: string, code: string): Promise<void> {
  const user = getCognitoUser(email)

  return new Promise((resolve, reject) => {
    user.confirmRegistration(code, true, (err) => {
      if (err) {
        reject(err)
        return
      }
      resolve()
    })
  })
}

export function signIn(email: string, password: string): Promise<CognitoUserSession> {
  const user = getCognitoUser(email)
  const details = new AuthenticationDetails({
    Username: email,
    Password: password,
  })

  return new Promise((resolve, reject) => {
    user.authenticateUser(details, {
      onSuccess: (session) => resolve(session),
      onFailure: (err) => reject(err),
    })
  })
}

export function forgotPassword(email: string): Promise<void> {
  const user = getCognitoUser(email)

  return new Promise((resolve, reject) => {
    user.forgotPassword({
      onSuccess: () => resolve(),
      onFailure: (err) => reject(err),
      inputVerificationCode: () => resolve(),
    })
  })
}

export function confirmForgotPassword(
  email: string,
  code: string,
  newPassword: string,
): Promise<void> {
  const user = getCognitoUser(email)

  return new Promise((resolve, reject) => {
    user.confirmPassword(code, newPassword, {
      onSuccess: () => resolve(),
      onFailure: (err) => reject(err),
    })
  })
}

export function signOut(): void {
  if (!isCognitoConfigured()) return
  getUserPool().getCurrentUser()?.signOut()
}

/** Federated / Hosted UI logout (clears Cognito cookies for the domain). */
export function hostedUiSignOut(): void {
  signOut()
  if (!isHostedUiConfigured()) return

  const logoutUri = encodeURIComponent(`${window.location.origin}/`)
  const url =
    `${cognitoHostedUiBaseUrl()}/logout` +
    `?client_id=${encodeURIComponent(env.cognitoClientId)}` +
    `&logout_uri=${logoutUri}`
  window.location.assign(url)
}

export function sessionToUser(session: CognitoUserSession): AuthUser {
  const payload = session.getIdToken().decodePayload()
  return {
    email: String(payload.email ?? payload['cognito:username'] ?? ''),
    sub: String(payload.sub ?? ''),
  }
}

function persistOAuthSession(tokens: {
  id_token: string
  access_token: string
  refresh_token?: string
}): CognitoUserSession {
  const session = new CognitoUserSession({
    IdToken: new CognitoIdToken({ IdToken: tokens.id_token }),
    AccessToken: new CognitoAccessToken({ AccessToken: tokens.access_token }),
    RefreshToken: new CognitoRefreshToken({
      RefreshToken: tokens.refresh_token ?? '',
    }),
  })

  const payload = session.getAccessToken().decodePayload()
  const username = String(payload.username ?? payload.sub ?? '')
  const user = new CognitoUser({
    Username: username,
    Pool: getUserPool(),
  })
  user.setSignInUserSession(session)
  return session
}

export async function startHostedUiSignIn(
  identityProvider?: 'Google' | 'COGNITO',
): Promise<void> {
  if (!isHostedUiConfigured()) {
    throw new Error(
      'Hosted UI is not configured. Set VITE_COGNITO_DOMAIN and enable_hosted_ui in infra.',
    )
  }

  const { url } = await buildAuthorizeUrl({
    identityProvider,
    redirectUri: oauthRedirectUri(),
  })
  window.location.assign(url)
}

export async function completeOAuthCallback(code: string): Promise<CognitoUserSession> {
  const tokens = await exchangeAuthorizationCode(code, oauthRedirectUri())
  clearPkceSession()
  return persistOAuthSession(tokens)
}
