import {
  pgTable,
  serial,
  integer,
  varchar,
  text,
  timestamp,
  uuid,
  boolean,
  jsonb,
  index,
} from "drizzle-orm/pg-core";

// -------------------------
// users
// -------------------------
export const users = pgTable("users", {
  id: serial("id").primaryKey(),

  username: varchar("username", { length: 50 })
    .notNull()
    .unique(),

  password: text("password").notNull(),

  createdAt: timestamp("created_at")
    .notNull()
    .defaultNow(),
});

// -------------------------
// sessions
// -------------------------
export const sessions = pgTable("sessions", {
  id: uuid("id").primaryKey().defaultRandom(),

  userId: integer("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),

  expiresAt: timestamp("expires_at").notNull(),

  createdAt: timestamp("created_at")
    .notNull()
    .defaultNow(),
});

// -------------------------
// games：游戏记录表
// -------------------------
export const games = pgTable(
  "games",
  {
    gameId: uuid("game_id").primaryKey(),

    userId: integer("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),

    player: integer("player").notNull(),

    cells: jsonb("cells")
      .$type<number[]>()
      .notNull(),

    gameRunning: boolean("game_running").notNull(),

    winningPattern: jsonb("winning_pattern")
      .$type<number[] | null>(),
  },
  (table) => [
    index("idx_games_user_id").on(table.userId),
  ]
);
