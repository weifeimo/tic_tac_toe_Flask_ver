import {
  pgTable,
  serial,
  varchar,
  text,
  timestamp,
  uuid,
  integer,
  index,
} from 'drizzle-orm/pg-core'

// Users table
export const users = pgTable('users', {
  id: serial('id').primaryKey(),

  username: varchar('username', { length: 50 })
    .notNull()
    .unique(),

  password: text('password').notNull(),

  createdAt: timestamp('created_at', {
    withTimezone: true,
  })
    .defaultNow()
    .notNull(),
})

// Sessions table
export const sessions = pgTable(
  'sessions',
  {
    id: uuid('id').defaultRandom().primaryKey(),

    userId: integer('user_id')
      .notNull()
      .references(() => users.id, {
        onDelete: 'cascade',
      }),

    expiresAt: timestamp('expires_at', {
      withTimezone: true,
    }).notNull(),

    createdAt: timestamp('created_at', {
      withTimezone: true,
    })
      .defaultNow()
      .notNull(),
  },
  (table) => [
    index('sessions_user_id_idx').on(table.userId),
  ],
)