import { pgTable, text, serial, integer, boolean, timestamp, vector, jsonb, doublePrecision } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  role: text("role").notNull().default("user"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const conversations = pgTable("conversations", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id).notNull(),
  title: text("title"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const messages = pgTable("messages", {
  id: serial("id").primaryKey(),
  conversationId: integer("conversation_id").references(() => conversations.id).notNull(),
  userId: integer("user_id").references(() => users.id),
  role: text("role").notNull(), // 'user' or 'assistant'
  agentType: text("agent_type"),
  content: text("content").notNull(),
  metadata: jsonb("metadata").default({}),
  tokenCount: integer("token_count").default(0),
  createdAt: timestamp("created_at").defaultNow(),
});

export const memories = pgTable("memories", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id).notNull(),
  content: text("content").notNull(),
  embedding: vector("embedding", { dimensions: 1536 }),
  metadata: jsonb("metadata"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const files = pgTable("files", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id).notNull(),
  filename: text("filename").notNull(),
  path: text("path").notNull(),
  size: integer("size"),
  mimeType: text("mime_type"),
  metadata: jsonb("metadata"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const agentConfigs = pgTable("agent_configs", {
  id: serial("id").primaryKey(),
  name: text("name").notNull().unique(),
  description: text("description"),
  systemPrompt: text("system_prompt").notNull(),
  isActive: boolean("is_active").default(true),
  capabilities: jsonb("capabilities"),
  email: text("email"),
  phone: text("phone"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const emailDrafts = pgTable("email_drafts", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id).notNull(),
  conversationId: integer("conversation_id").references(() => conversations.id).notNull(),
  agentType: text("agent_type").notNull(),
  to: text("to").notNull(),
  subject: text("subject").notNull(),
  content: text("content").notNull(),
  htmlContent: text("html_content"),
  status: text("status").notNull().default("pending"), // pending, approved, rejected, sent, failed
  originalRequest: text("original_request").notNull(),
  editInstructions: text("edit_instructions"),
  metadata: jsonb("metadata"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
  sentAt: timestamp("sent_at"),
});

export const emailTemplates = pgTable("email_templates", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id).notNull(),
  name: text("name").notNull(),
  subject: text("subject").notNull(),
  content: text("content").notNull(),
  htmlContent: text("html_content"),
  variables: jsonb("variables"),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const reportTemplates = pgTable("report_templates", {
  id: text("id").primaryKey(),
  dealerEmail: text("dealer_email").notNull(),
  name: text("name").notNull(),
  type: text("type").notNull().$type<'sales_performance' | 'profit_analysis' | 'lead_source_roi' | 'inventory_analysis' | 'custom'>(),
  schedule: text("schedule").notNull().$type<'daily' | 'weekly' | 'monthly' | 'quarterly'>(),
  dayOfWeek: integer("day_of_week"),
  dayOfMonth: integer("day_of_month"),
  recipients: jsonb("recipients").$type<string[]>().notNull(),
  metrics: jsonb("metrics").$type<string[]>().notNull(),
  filters: jsonb("filters").$type<Record<string, any>>().default({}),
  formatOptions: jsonb("format_options").$type<{
    includeCharts: boolean;
    includeTables: boolean;
    includeInsights: boolean;
    pdfFormat: boolean;
  }>().notNull(),
  isActive: boolean("is_active").default(true),
  lastRun: timestamp("last_run"),
  nextRun: timestamp("next_run"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Insert schemas
export const insertUserSchema = createInsertSchema(users).omit({
  id: true,
  createdAt: true,
});

export const insertConversationSchema = createInsertSchema(conversations).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertMessageSchema = createInsertSchema(messages).omit({
  id: true,
  createdAt: true,
});

export const insertMemorySchema = createInsertSchema(memories).omit({
  id: true,
  createdAt: true,
});

export const insertFileSchema = createInsertSchema(files).omit({
  id: true,
  createdAt: true,
});

export const insertAgentConfigSchema = createInsertSchema(agentConfigs).omit({
  id: true,
  createdAt: true,
});

export const insertEmailDraftSchema = createInsertSchema(emailDrafts).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
  sentAt: true,
});

export const insertEmailTemplateSchema = createInsertSchema(emailTemplates).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertReportTemplateSchema = createInsertSchema(reportTemplates).omit({
  createdAt: true,
  updatedAt: true,
  lastRun: true,
  nextRun: true,
});

// Types
export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;

export type Conversation = typeof conversations.$inferSelect;
export type InsertConversation = z.infer<typeof insertConversationSchema>;

export type Message = typeof messages.$inferSelect;
export type InsertMessage = z.infer<typeof insertMessageSchema>;

export type Memory = typeof memories.$inferSelect;
export type InsertMemory = z.infer<typeof insertMemorySchema>;

export type File = typeof files.$inferSelect;
export type InsertFile = z.infer<typeof insertFileSchema>;

export type AgentConfig = typeof agentConfigs.$inferSelect;
export type InsertAgentConfig = z.infer<typeof insertAgentConfigSchema>;

export type EmailDraft = typeof emailDrafts.$inferSelect;
export type InsertEmailDraft = z.infer<typeof insertEmailDraftSchema>;

export type EmailTemplate = typeof emailTemplates.$inferSelect;
export type InsertEmailTemplate = z.infer<typeof insertEmailTemplateSchema>;

export type ReportTemplate = typeof reportTemplates.$inferSelect;
export type InsertReportTemplate = z.infer<typeof insertReportTemplateSchema>;
