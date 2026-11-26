'use client'

import { signup } from '@/app/actions/auth'
import { useActionState } from 'react'
import styles from "@/components/game.module.css";

export default function SignupForm() {
  const [state, action, pending] = useActionState(signup, undefined)

  return (
    <form action={action}>
        <div className={styles.card}>
          <label htmlFor="name">Name </label>
          <input
            id="name"
            name="name"
            placeholder="user"
            autoComplete="username"
          />
        </div>

        <div className={styles.card}>
          <label htmlFor="password">Password </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
          />
        </div>

        <div className={styles.card2}>
          {state?.errors?.name && <p className={styles.errors}>{state.errors.name}</p>}
          {state?.errors?.password && (
            <div className={styles.errors}>
              <p>Password must:</p>
              <ul className={styles.errorList}>
                {state.errors.password.map((error) => (
                  <li key={error}>- {error}</li>
                ))}
              </ul>
            </div>
          )}
          {state?.message && <p className={styles.errors} role="alert">{state.message}</p>}
        </div>


      <button disabled={pending} type="submit" className={styles.submit}>
        {pending ? 'Signing up...' : 'Submit'}
      </button>
    </form>
  )
}