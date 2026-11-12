'use client'

import { signup } from '@/app/actions/auth'
import { useActionState } from 'react'
import styles from "@/components/game.module.css";

export default function SignupForm() {
  const [state, action, pending] = useActionState(signup, undefined)

  return (
    <form action={action}>
        <div>
          <label htmlFor="name">Name</label>
          <input
            id="name"
            name="name"
            placeholder="Name"
            autoComplete="username"
          />
        </div>
        {state?.errors?.name && <p>{state.errors.name}</p>}

        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
          />
        </div>
        {state?.errors?.password && (
          <div>
            <p>Password must:</p>
            <ul>
              {state.errors.password.map((error) => (
                <li key={error}>- {error}</li>
              ))}
            </ul>
          </div>
        )}

      {state?.message && <p role="alert">{state.message}</p>}

      <button disabled={pending} type="submit" className={styles.restart}>
        {pending ? 'Signing up...' : 'Confirm'}
      </button>
    </form>
  )
}