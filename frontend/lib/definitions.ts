import * as z from 'zod'

export const SignupFormSchema = z.object({
  name: z
    .string()
    .trim() //先に空白を取り除く
    .min(2, { error: 'Name must be at least 2 characters long.' }),
  password: z
    .string()
    .min(8, { error: 'Be at least 8 characters long' })
    .regex(/[a-zA-Z]/, { error: 'Contain at least one letter.' })
    .regex(/[0-9]/, { error: 'Contain at least one number.' })
    .regex(/[^a-zA-Z0-9]/, {
      error: 'Contain at least one special character.',
    })
})

export type FormState =
  | {
      errors?: {
        name?: string[]
        password?: string[]
      }
      message?: string
    }
  | undefined

// JWT に入れる内容。DB の sessions.id（uuid）を指す
export type SessionPayload = {
  sessionId: string
  expiresAt: Date
}