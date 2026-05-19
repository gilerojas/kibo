create schema if not exists kibo;

create table if not exists kibo.users (
    id uuid primary key default gen_random_uuid(),
    telegram_user_id bigint not null unique,
    telegram_chat_id bigint not null,
    name text,
    email text,
    timezone text not null default 'America/Santo_Domingo',
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists kibo.commands (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references kibo.users(id) on delete set null,
    telegram_chat_id bigint,
    telegram_user_id bigint,
    telegram_message_id bigint,
    raw_text text not null,
    intent text not null,
    status text not null,
    parsed_payload jsonb not null default '{}'::jsonb,
    source text not null default 'telegram',
    created_at timestamptz not null default now(),
    processed_at timestamptz,
    error_message text
);

create table if not exists kibo.actions (
    id uuid primary key default gen_random_uuid(),
    command_id uuid not null references kibo.commands(id) on delete cascade,
    user_id uuid references kibo.users(id) on delete set null,
    action_type text not null,
    destination text not null,
    external_id text,
    external_url text,
    status text not null,
    created_at timestamptz not null default now(),
    error_message text
);

create table if not exists kibo.notion_objects (
    id uuid primary key default gen_random_uuid(),
    command_id uuid references kibo.commands(id) on delete cascade,
    action_id uuid references kibo.actions(id) on delete cascade,
    notion_page_id text not null,
    notion_url text,
    notion_database_id text,
    object_type text not null,
    created_at timestamptz not null default now()
);

create index if not exists users_telegram_user_id_idx
    on kibo.users (telegram_user_id);

create index if not exists commands_user_created_at_idx
    on kibo.commands (user_id, created_at desc);

create index if not exists commands_intent_status_idx
    on kibo.commands (intent, status);

create index if not exists actions_command_id_idx
    on kibo.actions (command_id);

create index if not exists notion_objects_command_id_idx
    on kibo.notion_objects (command_id);
