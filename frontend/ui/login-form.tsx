'use client'

import { login } from '@/app/actions/auth'
import { useActionState } from 'react'
import styles from "@/components/game.module.css";

export default function LoginForm() {
  const [state, action, pending] = useActionState(login, undefined)

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
        {state?.errors?.name && <p>{state.errors.name}</p>}

        <div className={styles.card}>
          <label htmlFor="password">Password </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
          />
        </div>
        {state?.errors?.password && <p>{state.errors.password}</p>}
        {state?.message && <p role="alert">{state.message}</p>}

      <button disabled={pending} type="submit" className={styles.submit}>
        {pending ? 'Logging in...' : 'Confirm'}
      </button>
    </form>
  )
}