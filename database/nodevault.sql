/*
 Navicat Premium Dump SQL

 Source Server Type    : PostgreSQL
 Source Server Version : 170007 (170007)
 Target Server Type    : PostgreSQL
 Target Server Version : 170007 (170007)
 File Encoding         : 65001

 Date: 29/03/2026 (updated to match current schema)
*/


-- ----------------------------
-- Sequence structure for node_tags_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."node_tags_id_seq" CASCADE;
CREATE SEQUENCE "public"."node_tags_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Table structure for alembic_version
-- ----------------------------
DROP TABLE IF EXISTS "public"."alembic_version" CASCADE;
CREATE TABLE "public"."alembic_version" (
  "version_num" varchar(32) COLLATE "pg_catalog"."default" NOT NULL
);

-- ----------------------------
-- Table structure for api_keys
-- ----------------------------
DROP TABLE IF EXISTS "public"."api_keys" CASCADE;
CREATE TABLE "public"."api_keys" (
  "id" uuid NOT NULL,
  "name" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "key_prefix" varchar(12) COLLATE "pg_catalog"."default" NOT NULL,
  "key_hash" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "owner_id" uuid NOT NULL,
  "is_active" bool NOT NULL DEFAULT true,
  "created_at" timestamp(6) NOT NULL DEFAULT now(),
  "last_used_at" timestamp(6)
);

-- ----------------------------
-- Table structure for categories
-- ----------------------------
DROP TABLE IF EXISTS "public"."categories" CASCADE;
CREATE TABLE "public"."categories" (
  "id" uuid NOT NULL DEFAULT gen_random_uuid(),
  "name" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "display_name" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "icon" varchar(64) COLLATE "pg_catalog"."default",
  "sort_order" int4 NOT NULL DEFAULT 0,
  "is_default" bool NOT NULL DEFAULT false,
  "created_by" uuid,
  "created_at" timestamp(6) NOT NULL DEFAULT now()
);

-- ----------------------------
-- Table structure for credential_token_cache
-- ----------------------------
DROP TABLE IF EXISTS "public"."credential_token_cache" CASCADE;
CREATE TABLE "public"."credential_token_cache" (
  "id" uuid NOT NULL,
  "credential_id" uuid NOT NULL,
  "access_token" text COLLATE "pg_catalog"."default" NOT NULL,
  "expires_at" timestamp(6),
  "created_at" timestamp(6) NOT NULL DEFAULT now()
);

-- ----------------------------
-- Table structure for departments  (renamed from namespaces)
-- ----------------------------
DROP TABLE IF EXISTS "public"."departments" CASCADE;
CREATE TABLE "public"."departments" (
  "id" uuid NOT NULL DEFAULT gen_random_uuid(),
  "slug" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "display_name" varchar(256) COLLATE "pg_catalog"."default",
  "description" text COLLATE "pg_catalog"."default",
  "owner_id" uuid NOT NULL,
  "created_at" timestamp(6) NOT NULL DEFAULT now()
);

-- ----------------------------
-- Table structure for department_members  (renamed from namespace_members)
-- ----------------------------
DROP TABLE IF EXISTS "public"."department_members" CASCADE;
CREATE TABLE "public"."department_members" (
  "id" uuid NOT NULL DEFAULT gen_random_uuid(),
  "department_id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "role" varchar(32) COLLATE "pg_catalog"."default" NOT NULL DEFAULT 'member'::character varying,
  "status" varchar(16) COLLATE "pg_catalog"."default" NOT NULL DEFAULT 'active'::character varying,
  "joined_at" timestamp(6) NOT NULL DEFAULT now()
);

-- ----------------------------
-- Table structure for discovery_sessions
-- ----------------------------
DROP TABLE IF EXISTS "public"."discovery_sessions" CASCADE;
CREATE TABLE "public"."discovery_sessions" (
  "id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "base_url" varchar(2048) COLLATE "pg_catalog"."default",
  "source" varchar(16) COLLATE "pg_catalog"."default" NOT NULL DEFAULT 'probe'::character varying,
  "status" varchar(16) COLLATE "pg_catalog"."default" NOT NULL DEFAULT 'probing'::character varying,
  "spec_url" varchar(2048) COLLATE "pg_catalog"."default",
  "total_operations" int4,
  "imported_count" int4 NOT NULL DEFAULT 0,
  "created_at" timestamp(6) NOT NULL DEFAULT now(),
  "completed_at" timestamp(6)
);

-- ----------------------------
-- Table structure for node_invocation_logs
-- ----------------------------
DROP TABLE IF EXISTS "public"."node_invocation_logs" CASCADE;
CREATE TABLE "public"."node_invocation_logs" (
  "id" uuid NOT NULL,
  "node_id" uuid NOT NULL,
  "version" varchar(32) COLLATE "pg_catalog"."default",
  "invoked_by" uuid,
  "input_data" jsonb,
  "output_data" jsonb,
  "status" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "latency_ms" int4,
  "error_message" text COLLATE "pg_catalog"."default",
  "created_at" timestamp(6) NOT NULL
);

-- ----------------------------
-- Table structure for node_tags
-- ----------------------------
DROP TABLE IF EXISTS "public"."node_tags" CASCADE;
CREATE TABLE "public"."node_tags" (
  "id" int4 NOT NULL DEFAULT nextval('node_tags_id_seq'::regclass),
  "node_id" uuid NOT NULL,
  "tag" varchar(64) COLLATE "pg_catalog"."default" NOT NULL
);

-- ----------------------------
-- Table structure for node_versions
-- ----------------------------
DROP TABLE IF EXISTS "public"."node_versions" CASCADE;
CREATE TABLE "public"."node_versions" (
  "id" uuid NOT NULL,
  "node_id" uuid NOT NULL,
  "version" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "input_schema" jsonb NOT NULL,
  "output_schema" jsonb NOT NULL,
  "runtime_config" jsonb NOT NULL,
  "changelog" text COLLATE "pg_catalog"."default",
  "is_default" bool NOT NULL,
  "is_deprecated" bool NOT NULL,
  "created_at" timestamp(6) NOT NULL,
  "created_by" uuid
);

-- ----------------------------
-- Table structure for nodes
-- ----------------------------
DROP TABLE IF EXISTS "public"."nodes" CASCADE;
CREATE TABLE "public"."nodes" (
  "id" uuid NOT NULL,
  "name" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "department_id" uuid NOT NULL,
  "owner_id" uuid NOT NULL,
  "display_name" varchar(256) COLLATE "pg_catalog"."default",
  "description" text COLLATE "pg_catalog"."default",
  "status" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "visibility" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "created_at" timestamp(6) NOT NULL,
  "updated_at" timestamp(6) NOT NULL,
  "invocation_count" int4 NOT NULL DEFAULT 0,
  "source_credential_id" uuid,
  "source_path" varchar(512) COLLATE "pg_catalog"."default",
  "discovery_session_id" uuid,
  "category_id" uuid NOT NULL
);

-- ----------------------------
-- Table structure for role_applications  (new)
-- ----------------------------
DROP TABLE IF EXISTS "public"."role_applications" CASCADE;
CREATE TABLE "public"."role_applications" (
  "id" uuid NOT NULL DEFAULT gen_random_uuid(),
  "user_id" uuid NOT NULL,
  "requested_role" int4 NOT NULL,
  "status" varchar(16) COLLATE "pg_catalog"."default" NOT NULL DEFAULT 'pending'::character varying,
  "reason" text COLLATE "pg_catalog"."default",
  "review_note" text COLLATE "pg_catalog"."default",
  "reviewed_by" uuid,
  "created_at" timestamp(6) NOT NULL DEFAULT now(),
  "reviewed_at" timestamp(6)
);

-- ----------------------------
-- Table structure for service_credentials
-- ----------------------------
DROP TABLE IF EXISTS "public"."service_credentials" CASCADE;
CREATE TABLE "public"."service_credentials" (
  "id" uuid NOT NULL,
  "owner_id" uuid NOT NULL,
  "name" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "base_url" varchar(2048) COLLATE "pg_catalog"."default" NOT NULL,
  "auth_type" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "login_endpoint" varchar(2048) COLLATE "pg_catalog"."default",
  "login_method" varchar(8) COLLATE "pg_catalog"."default" DEFAULT 'POST'::character varying,
  "login_body_template" text COLLATE "pg_catalog"."default",
  "credential_encrypted" bytea,
  "credential_nonce" bytea,
  "token_json_path" varchar(256) COLLATE "pg_catalog"."default",
  "token_ttl" int4,
  "static_token_encrypted" bytea,
  "static_token_nonce" bytea,
  "api_key_header" varchar(128) COLLATE "pg_catalog"."default" DEFAULT 'X-API-Key'::character varying,
  "api_key_encrypted" bytea,
  "api_key_nonce" bytea,
  "created_at" timestamp(6) NOT NULL DEFAULT now(),
  "updated_at" timestamp(6) NOT NULL DEFAULT now()
);

-- ----------------------------
-- Table structure for skill_nodes
-- ----------------------------
DROP TABLE IF EXISTS "public"."skill_nodes" CASCADE;
CREATE TABLE "public"."skill_nodes" (
  "id" uuid NOT NULL DEFAULT gen_random_uuid(),
  "skill_id" uuid NOT NULL,
  "node_id" uuid NOT NULL,
  "usage_hint" varchar(500) COLLATE "pg_catalog"."default",
  "sort_order" int4 NOT NULL DEFAULT 0,
  "created_at" timestamp(6) NOT NULL DEFAULT now()
);

-- ----------------------------
-- Table structure for skill_versions
-- ----------------------------
DROP TABLE IF EXISTS "public"."skill_versions" CASCADE;
CREATE TABLE "public"."skill_versions" (
  "id" uuid NOT NULL,
  "skill_id" uuid NOT NULL,
  "version" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "skill_md" text COLLATE "pg_catalog"."default" NOT NULL,
  "node_snapshot" jsonb NOT NULL DEFAULT '[]'::jsonb,
  "release_notes" text COLLATE "pg_catalog"."default",
  "is_default" bool NOT NULL DEFAULT false,
  "created_at" timestamp(6) NOT NULL DEFAULT now()
);

-- ----------------------------
-- Table structure for skills
-- ----------------------------
DROP TABLE IF EXISTS "public"."skills" CASCADE;
CREATE TABLE "public"."skills" (
  "id" uuid NOT NULL,
  "name" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "display_name" varchar(256) COLLATE "pg_catalog"."default",
  "description" text COLLATE "pg_catalog"."default",
  "owner_id" uuid NOT NULL,
  "status" varchar(32) COLLATE "pg_catalog"."default" NOT NULL DEFAULT 'active'::character varying,
  "is_stale" bool NOT NULL DEFAULT false,
  "created_at" timestamp(6) NOT NULL DEFAULT now(),
  "updated_at" timestamp(6) NOT NULL DEFAULT now(),
  "is_system" bool NOT NULL DEFAULT false
);

-- ----------------------------
-- Table structure for system_settings  (new)
-- ----------------------------
DROP TABLE IF EXISTS "public"."system_settings" CASCADE;
CREATE TABLE "public"."system_settings" (
  "key" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "value" text COLLATE "pg_catalog"."default",
  "updated_at" timestamp(6) NOT NULL DEFAULT now()
);

-- ----------------------------
-- Table structure for user_ai_configs
-- ----------------------------
DROP TABLE IF EXISTS "public"."user_ai_configs" CASCADE;
CREATE TABLE "public"."user_ai_configs" (
  "id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "name" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "provider" varchar(32) COLLATE "pg_catalog"."default" NOT NULL DEFAULT 'openai'::character varying,
  "model" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "api_key_encrypted" bytea NOT NULL,
  "api_key_nonce" bytea NOT NULL,
  "base_url" varchar(512) COLLATE "pg_catalog"."default",
  "is_default" bool NOT NULL DEFAULT false,
  "created_at" timestamp(6) NOT NULL,
  "updated_at" timestamp(6) NOT NULL
);

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS "public"."users" CASCADE;
CREATE TABLE "public"."users" (
  "id" uuid NOT NULL,
  "email" varchar(256) COLLATE "pg_catalog"."default" NOT NULL,
  "username" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "hashed_password" varchar(256) COLLATE "pg_catalog"."default" NOT NULL,
  "is_active" bool NOT NULL DEFAULT true,
  "role" int4 NOT NULL DEFAULT 2,
  "display_name" varchar(128) COLLATE "pg_catalog"."default",
  "avatar_url" varchar(512) COLLATE "pg_catalog"."default",
  "bio" text COLLATE "pg_catalog"."default",
  "phone" varchar(32) COLLATE "pg_catalog"."default",
  "title" varchar(128) COLLATE "pg_catalog"."default",
  "created_at" timestamp(6) NOT NULL DEFAULT now(),
  "updated_at" timestamp(6) NOT NULL DEFAULT now()
);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."node_tags_id_seq"
OWNED BY "public"."node_tags"."id";

-- ----------------------------
-- Primary Key structure for table alembic_version
-- ----------------------------
ALTER TABLE "public"."alembic_version" ADD CONSTRAINT "alembic_version_pkc" PRIMARY KEY ("version_num");

-- ----------------------------
-- Indexes structure for table api_keys
-- ----------------------------
CREATE UNIQUE INDEX "ix_api_keys_key_hash" ON "public"."api_keys" USING btree (
  "key_hash" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "ix_api_keys_owner_id" ON "public"."api_keys" USING btree (
  "owner_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table api_keys
-- ----------------------------
ALTER TABLE "public"."api_keys" ADD CONSTRAINT "api_keys_key_hash_key" UNIQUE ("key_hash");

-- ----------------------------
-- Primary Key structure for table api_keys
-- ----------------------------
ALTER TABLE "public"."api_keys" ADD CONSTRAINT "api_keys_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table categories
-- ----------------------------
CREATE UNIQUE INDEX "ix_categories_name" ON "public"."categories" USING btree (
  "name" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table categories
-- ----------------------------
ALTER TABLE "public"."categories" ADD CONSTRAINT "categories_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table credential_token_cache
-- ----------------------------
CREATE UNIQUE INDEX "ix_credential_token_cache_credential_id" ON "public"."credential_token_cache" USING btree (
  "credential_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table credential_token_cache
-- ----------------------------
ALTER TABLE "public"."credential_token_cache" ADD CONSTRAINT "credential_token_cache_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table departments
-- ----------------------------
CREATE UNIQUE INDEX "ix_departments_slug" ON "public"."departments" USING btree (
  "slug" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table departments
-- ----------------------------
ALTER TABLE "public"."departments" ADD CONSTRAINT "departments_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table department_members
-- ----------------------------
CREATE INDEX "ix_department_members_department_id" ON "public"."department_members" USING btree (
  "department_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE INDEX "ix_department_members_user_id" ON "public"."department_members" USING btree (
  "user_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE INDEX "ix_department_members_status" ON "public"."department_members" USING btree (
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table department_members
-- ----------------------------
ALTER TABLE "public"."department_members" ADD CONSTRAINT "uq_department_member" UNIQUE ("department_id", "user_id");

-- ----------------------------
-- Primary Key structure for table department_members
-- ----------------------------
ALTER TABLE "public"."department_members" ADD CONSTRAINT "department_members_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table discovery_sessions
-- ----------------------------
CREATE INDEX "ix_discovery_sessions_status" ON "public"."discovery_sessions" USING btree (
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "ix_discovery_sessions_user_id" ON "public"."discovery_sessions" USING btree (
  "user_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table discovery_sessions
-- ----------------------------
ALTER TABLE "public"."discovery_sessions" ADD CONSTRAINT "discovery_sessions_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table node_invocation_logs
-- ----------------------------
CREATE INDEX "ix_invocation_logs_node_created" ON "public"."node_invocation_logs" USING btree (
  "node_id" "pg_catalog"."uuid_ops" ASC NULLS LAST,
  "created_at" "pg_catalog"."timestamp_ops" ASC NULLS LAST
);
CREATE INDEX "ix_node_invocation_logs_created_at" ON "public"."node_invocation_logs" USING btree (
  "created_at" "pg_catalog"."timestamp_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table node_invocation_logs
-- ----------------------------
ALTER TABLE "public"."node_invocation_logs" ADD CONSTRAINT "node_invocation_logs_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table node_tags
-- ----------------------------
CREATE INDEX "ix_node_tags_node_id" ON "public"."node_tags" USING btree (
  "node_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE INDEX "ix_node_tags_tag" ON "public"."node_tags" USING btree (
  "tag" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table node_tags
-- ----------------------------
ALTER TABLE "public"."node_tags" ADD CONSTRAINT "uq_node_tag" UNIQUE ("node_id", "tag");

-- ----------------------------
-- Primary Key structure for table node_tags
-- ----------------------------
ALTER TABLE "public"."node_tags" ADD CONSTRAINT "node_tags_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table node_versions
-- ----------------------------
CREATE UNIQUE INDEX "uq_node_default_version" ON "public"."node_versions" USING btree (
  "node_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
) WHERE is_default = true;

-- ----------------------------
-- Uniques structure for table node_versions
-- ----------------------------
ALTER TABLE "public"."node_versions" ADD CONSTRAINT "uq_node_version" UNIQUE ("node_id", "version");

-- ----------------------------
-- Primary Key structure for table node_versions
-- ----------------------------
ALTER TABLE "public"."node_versions" ADD CONSTRAINT "node_versions_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table nodes
-- ----------------------------
CREATE INDEX "ix_nodes_category_id" ON "public"."nodes" USING btree (
  "category_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE INDEX "ix_nodes_department_id" ON "public"."nodes" USING btree (
  "department_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE INDEX "ix_nodes_discovery_session_id" ON "public"."nodes" USING btree (
  "discovery_session_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE INDEX "ix_nodes_name" ON "public"."nodes" USING btree (
  "name" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "ix_nodes_source_credential_id" ON "public"."nodes" USING btree (
  "source_credential_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE INDEX "ix_nodes_status" ON "public"."nodes" USING btree (
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table nodes
-- ----------------------------
ALTER TABLE "public"."nodes" ADD CONSTRAINT "uq_node_name_department" UNIQUE ("name", "department_id");

-- ----------------------------
-- Primary Key structure for table nodes
-- ----------------------------
ALTER TABLE "public"."nodes" ADD CONSTRAINT "nodes_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table role_applications
-- ----------------------------
CREATE INDEX "ix_role_applications_user_id" ON "public"."role_applications" USING btree (
  "user_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE INDEX "ix_role_applications_status" ON "public"."role_applications" USING btree (
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table role_applications
-- ----------------------------
ALTER TABLE "public"."role_applications" ADD CONSTRAINT "role_applications_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table service_credentials
-- ----------------------------
CREATE INDEX "ix_service_credentials_owner_id" ON "public"."service_credentials" USING btree (
  "owner_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table service_credentials
-- ----------------------------
ALTER TABLE "public"."service_credentials" ADD CONSTRAINT "service_credentials_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table skill_nodes
-- ----------------------------
CREATE INDEX "ix_skill_nodes_node_id" ON "public"."skill_nodes" USING btree (
  "node_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE INDEX "ix_skill_nodes_skill_id" ON "public"."skill_nodes" USING btree (
  "skill_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table skill_nodes
-- ----------------------------
ALTER TABLE "public"."skill_nodes" ADD CONSTRAINT "uq_skill_node" UNIQUE ("skill_id", "node_id");

-- ----------------------------
-- Primary Key structure for table skill_nodes
-- ----------------------------
ALTER TABLE "public"."skill_nodes" ADD CONSTRAINT "skill_nodes_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table skill_versions
-- ----------------------------
CREATE INDEX "ix_skill_versions_skill_id" ON "public"."skill_versions" USING btree (
  "skill_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);
CREATE UNIQUE INDEX "uq_skill_default_version" ON "public"."skill_versions" USING btree (
  "skill_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
) WHERE is_default = true;

-- ----------------------------
-- Uniques structure for table skill_versions
-- ----------------------------
ALTER TABLE "public"."skill_versions" ADD CONSTRAINT "uq_skill_version" UNIQUE ("skill_id", "version");

-- ----------------------------
-- Primary Key structure for table skill_versions
-- ----------------------------
ALTER TABLE "public"."skill_versions" ADD CONSTRAINT "skill_versions_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table skills
-- ----------------------------
CREATE INDEX "ix_skills_name" ON "public"."skills" USING btree (
  "name" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "ix_skills_status" ON "public"."skills" USING btree (
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table skills
-- ----------------------------
ALTER TABLE "public"."skills" ADD CONSTRAINT "uq_skill_name" UNIQUE ("name");

-- ----------------------------
-- Primary Key structure for table skills
-- ----------------------------
ALTER TABLE "public"."skills" ADD CONSTRAINT "skills_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table system_settings
-- ----------------------------
ALTER TABLE "public"."system_settings" ADD CONSTRAINT "system_settings_pkey" PRIMARY KEY ("key");

-- ----------------------------
-- Indexes structure for table user_ai_configs
-- ----------------------------
CREATE INDEX "ix_user_ai_configs_user_id" ON "public"."user_ai_configs" USING btree (
  "user_id" "pg_catalog"."uuid_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table user_ai_configs
-- ----------------------------
ALTER TABLE "public"."user_ai_configs" ADD CONSTRAINT "user_ai_configs_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table users
-- ----------------------------
CREATE UNIQUE INDEX "ix_users_email" ON "public"."users" USING btree (
  "email" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE UNIQUE INDEX "ix_users_username" ON "public"."users" USING btree (
  "username" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table users
-- ----------------------------
ALTER TABLE "public"."users" ADD CONSTRAINT "uq_user_email" UNIQUE ("email");

-- ----------------------------
-- Primary Key structure for table users
-- ----------------------------
ALTER TABLE "public"."users" ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Foreign Keys structure for table api_keys
-- ----------------------------
ALTER TABLE "public"."api_keys" ADD CONSTRAINT "api_keys_owner_id_fkey" FOREIGN KEY ("owner_id") REFERENCES "public"."users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table categories
-- ----------------------------
ALTER TABLE "public"."categories" ADD CONSTRAINT "categories_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table credential_token_cache
-- ----------------------------
ALTER TABLE "public"."credential_token_cache" ADD CONSTRAINT "credential_token_cache_credential_id_fkey" FOREIGN KEY ("credential_id") REFERENCES "public"."service_credentials" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table departments
-- ----------------------------
ALTER TABLE "public"."departments" ADD CONSTRAINT "departments_owner_id_fkey" FOREIGN KEY ("owner_id") REFERENCES "public"."users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table department_members
-- ----------------------------
ALTER TABLE "public"."department_members" ADD CONSTRAINT "department_members_department_id_fkey" FOREIGN KEY ("department_id") REFERENCES "public"."departments" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."department_members" ADD CONSTRAINT "department_members_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table discovery_sessions
-- ----------------------------
ALTER TABLE "public"."discovery_sessions" ADD CONSTRAINT "discovery_sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table node_invocation_logs
-- ----------------------------
ALTER TABLE "public"."node_invocation_logs" ADD CONSTRAINT "node_invocation_logs_invoked_by_fkey" FOREIGN KEY ("invoked_by") REFERENCES "public"."users" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;
ALTER TABLE "public"."node_invocation_logs" ADD CONSTRAINT "node_invocation_logs_node_id_fkey" FOREIGN KEY ("node_id") REFERENCES "public"."nodes" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table node_tags
-- ----------------------------
ALTER TABLE "public"."node_tags" ADD CONSTRAINT "node_tags_node_id_fkey" FOREIGN KEY ("node_id") REFERENCES "public"."nodes" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table node_versions
-- ----------------------------
ALTER TABLE "public"."node_versions" ADD CONSTRAINT "node_versions_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;
ALTER TABLE "public"."node_versions" ADD CONSTRAINT "node_versions_node_id_fkey" FOREIGN KEY ("node_id") REFERENCES "public"."nodes" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table nodes
-- ----------------------------
ALTER TABLE "public"."nodes" ADD CONSTRAINT "fk_nodes_category_id" FOREIGN KEY ("category_id") REFERENCES "public"."categories" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "public"."nodes" ADD CONSTRAINT "nodes_department_id_fkey" FOREIGN KEY ("department_id") REFERENCES "public"."departments" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."nodes" ADD CONSTRAINT "nodes_discovery_session_id_fkey" FOREIGN KEY ("discovery_session_id") REFERENCES "public"."discovery_sessions" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;
ALTER TABLE "public"."nodes" ADD CONSTRAINT "nodes_owner_id_fkey" FOREIGN KEY ("owner_id") REFERENCES "public"."users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."nodes" ADD CONSTRAINT "nodes_source_credential_id_fkey" FOREIGN KEY ("source_credential_id") REFERENCES "public"."service_credentials" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table role_applications
-- ----------------------------
ALTER TABLE "public"."role_applications" ADD CONSTRAINT "role_applications_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."role_applications" ADD CONSTRAINT "role_applications_reviewed_by_fkey" FOREIGN KEY ("reviewed_by") REFERENCES "public"."users" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table service_credentials
-- ----------------------------
ALTER TABLE "public"."service_credentials" ADD CONSTRAINT "service_credentials_owner_id_fkey" FOREIGN KEY ("owner_id") REFERENCES "public"."users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table skill_nodes
-- ----------------------------
ALTER TABLE "public"."skill_nodes" ADD CONSTRAINT "skill_nodes_node_id_fkey" FOREIGN KEY ("node_id") REFERENCES "public"."nodes" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."skill_nodes" ADD CONSTRAINT "skill_nodes_skill_id_fkey" FOREIGN KEY ("skill_id") REFERENCES "public"."skills" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table skill_versions
-- ----------------------------
ALTER TABLE "public"."skill_versions" ADD CONSTRAINT "skill_versions_skill_id_fkey" FOREIGN KEY ("skill_id") REFERENCES "public"."skills" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table skills
-- ----------------------------
ALTER TABLE "public"."skills" ADD CONSTRAINT "skills_owner_id_fkey" FOREIGN KEY ("owner_id") REFERENCES "public"."users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table user_ai_configs
-- ----------------------------
ALTER TABLE "public"."user_ai_configs" ADD CONSTRAINT "user_ai_configs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- ----------------------------
-- Default super admin user
-- ----------------------------
INSERT INTO "public"."users" ("id", "email", "username", "hashed_password", "is_active", "role", "display_name", "avatar_url", "bio", "phone", "title", "created_at", "updated_at")
VALUES ('1a6bde58-0f9e-4afb-b782-72d7b1e32a11', 'admin@admin.com', 'MJXJadmin', '$2b$12$szN2T26xSgdhpG/vBgHK8eoIpL4pgh6vDSFEBniYcfFpUfcIRqog6', true, 0, '超级管理员', NULL, NULL, NULL, NULL, '2026-03-24 01:48:45.300559', '2026-03-24 01:48:45.300559')
ON CONFLICT ("id") DO NOTHING;
