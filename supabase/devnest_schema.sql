-- DevNest Online / Teams schema for Supabase
-- Run this entire file once in Supabase Dashboard -> SQL Editor.
-- It is intentionally designed for a desktop client that ONLY has a publishable
-- (or legacy anon) key plus a signed-in user's JWT. Never put a service_role /
-- secret key in DevNest.

begin;

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Profiles
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    username text not null check (username ~ '^[A-Za-z0-9_][A-Za-z0-9_.-]{2,31}$'),
    first_name text not null check (char_length(first_name) between 1 and 80),
    last_name text not null check (char_length(last_name) between 1 and 80),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create unique index if not exists profiles_username_ci_uq on public.profiles (lower(username));

create or replace function public.handle_new_devnest_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    v_username text := trim(coalesce(new.raw_user_meta_data->>'username',''));
    v_first text := trim(coalesce(new.raw_user_meta_data->>'first_name',''));
    v_last text := trim(coalesce(new.raw_user_meta_data->>'last_name',''));
begin
    if v_username !~ '^[A-Za-z0-9_][A-Za-z0-9_.-]{2,31}$' then
        raise exception 'invalid DevNest username';
    end if;
    if char_length(v_first) not between 1 and 80 or char_length(v_last) not between 1 and 80 then
        raise exception 'invalid DevNest profile name';
    end if;
    insert into public.profiles(id, username, first_name, last_name)
    values (new.id, v_username, v_first, v_last)
    on conflict (id) do update set
        username=excluded.username, first_name=excluded.first_name,
        last_name=excluded.last_name, updated_at=now();
    return new;
end;
$$;

drop trigger if exists on_auth_user_created_devnest on auth.users;
create trigger on_auth_user_created_devnest
after insert on auth.users
for each row execute procedure public.handle_new_devnest_user();

-- ---------------------------------------------------------------------------
-- Personal cloud backup
-- ---------------------------------------------------------------------------
create table if not exists public.cloud_projects (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references public.profiles(id) on delete cascade,
    device_id text not null check (char_length(device_id) between 1 and 80),
    local_project_id bigint not null,
    name text not null check (char_length(name) between 1 and 200),
    description text not null default '' check (char_length(description) <= 5000),
    source_updated_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(owner_id, device_id, local_project_id)
);

create table if not exists public.cloud_resources (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references public.profiles(id) on delete cascade,
    project_id uuid not null references public.cloud_projects(id) on delete cascade,
    resource_type text not null check (resource_type in ('note','decision','architecture','repository')),
    local_key text not null check (char_length(local_key) between 1 and 160),
    title text not null default '' check (char_length(title) <= 500),
    payload jsonb not null default '{}'::jsonb check (octet_length(payload::text) <= 10485760),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(project_id, resource_type, local_key)
);
create index if not exists cloud_resources_project_idx on public.cloud_resources(project_id, resource_type);

-- Keep cloud identity columns stable. Team members may be allowed to edit project
-- metadata or resources, but they must never be able to take ownership of a row
-- by PATCHing owner_id/project_id through PostgREST.
create or replace function public.guard_devnest_cloud_project_identity()
returns trigger language plpgsql set search_path=public
as $$
begin
    if new.owner_id is distinct from old.owner_id
       or new.device_id is distinct from old.device_id
       or new.local_project_id is distinct from old.local_project_id then
        raise exception 'cloud project identity fields are immutable';
    end if;
    return new;
end;
$$;

drop trigger if exists devnest_cloud_project_identity_guard on public.cloud_projects;
create trigger devnest_cloud_project_identity_guard
before update on public.cloud_projects
for each row execute function public.guard_devnest_cloud_project_identity();

create or replace function public.guard_devnest_cloud_resource_identity()
returns trigger language plpgsql security definer set search_path=public
as $$
declare v_owner uuid;
begin
    if tg_op='UPDATE' and (
       new.project_id is distinct from old.project_id
       or new.resource_type is distinct from old.resource_type
       or new.local_key is distinct from old.local_key) then
        raise exception 'cloud resource identity fields are immutable';
    end if;
    select owner_id into v_owner from public.cloud_projects where id=new.project_id;
    if v_owner is null then raise exception 'cloud project not found'; end if;
    -- Never trust a desktop client supplied owner_id. The parent project is the
    -- source of truth, which prevents a team member from making themselves the
    -- owner of another person's resource.
    new.owner_id := v_owner;
    return new;
end;
$$;

drop trigger if exists devnest_cloud_resource_identity_guard on public.cloud_resources;
create trigger devnest_cloud_resource_identity_guard
before insert or update on public.cloud_resources
for each row execute function public.guard_devnest_cloud_resource_identity();

-- ---------------------------------------------------------------------------
-- Teams, roles and invitations
-- ---------------------------------------------------------------------------
create table if not exists public.teams (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references public.profiles(id) on delete cascade,
    name text not null check (char_length(name) between 2 and 80),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.team_roles (
    id uuid primary key default gen_random_uuid(),
    team_id uuid not null references public.teams(id) on delete cascade,
    name text not null check (char_length(name) between 1 and 80),
    rank integer not null check (rank between 1 and 999999),
    permissions jsonb not null default '{}'::jsonb,
    is_system boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(team_id, name),
    unique(team_id, rank)
);

alter table public.team_roles drop constraint if exists team_roles_team_id_rank_key;

create table if not exists public.team_members (
    team_id uuid not null references public.teams(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,
    role_id uuid references public.team_roles(id) on delete set null,
    joined_at timestamptz not null default now(),
    primary key(team_id, user_id)
);
create index if not exists team_members_user_idx on public.team_members(user_id, team_id);

create table if not exists public.team_invitations (
    id uuid primary key default gen_random_uuid(),
    team_id uuid not null references public.teams(id) on delete cascade,
    inviter_id uuid not null references public.profiles(id) on delete cascade,
    invitee_id uuid not null references public.profiles(id) on delete cascade,
    status text not null default 'pending' check (status in ('pending','accepted','declined','cancelled')),
    created_at timestamptz not null default now(),
    responded_at timestamptz,
    unique(team_id, invitee_id)
);

create table if not exists public.team_projects (
    team_id uuid not null references public.teams(id) on delete cascade,
    project_id uuid not null references public.cloud_projects(id) on delete cascade,
    assigned_by uuid not null references public.profiles(id) on delete cascade,
    assigned_at timestamptz not null default now(),
    primary key(team_id, project_id)
);

create table if not exists public.team_member_permission_overrides (
    team_id uuid not null references public.teams(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,
    permission_key text not null check (permission_key in (
        'view_project','edit_project','delete_project','create_note','edit_note','delete_note',
        'create_decision','edit_decision','delete_decision','edit_architecture',
        'manage_access','manage_roles','invite_members'
    )),
    allow boolean not null,
    updated_at timestamptz not null default now(),
    primary key(team_id, user_id, permission_key)
);

-- A resource policy switches a team resource into private/restricted mode.
-- ACL rows then define the users/roles allowed to see it. With restricted=true
-- and no ACL rows, only the cloud project owner can see it.
create table if not exists public.team_resource_policies (
    team_id uuid not null references public.teams(id) on delete cascade,
    project_id uuid not null references public.cloud_projects(id) on delete cascade,
    resource_type text not null check (resource_type in ('note','decision','architecture')),
    resource_key text not null,
    restricted boolean not null default true,
    updated_at timestamptz not null default now(),
    primary key(team_id, project_id, resource_type, resource_key)
);

create table if not exists public.team_resource_acl (
    id uuid primary key default gen_random_uuid(),
    team_id uuid not null references public.teams(id) on delete cascade,
    project_id uuid not null references public.cloud_projects(id) on delete cascade,
    resource_type text not null check (resource_type in ('note','decision','architecture')),
    resource_key text not null,
    subject_user_id uuid references public.profiles(id) on delete cascade,
    subject_role_id uuid references public.team_roles(id) on delete cascade,
    can_view boolean not null default true,
    can_edit boolean not null default false,
    created_at timestamptz not null default now(),
    check ((subject_user_id is not null)::int + (subject_role_id is not null)::int = 1)
);
create unique index if not exists team_resource_acl_user_uq
    on public.team_resource_acl(team_id,project_id,resource_type,resource_key,subject_user_id)
    where subject_user_id is not null;
create unique index if not exists team_resource_acl_role_uq
    on public.team_resource_acl(team_id,project_id,resource_type,resource_key,subject_role_id)
    where subject_role_id is not null;

-- Cross-department role visibility. A role always sees itself. Other roles are
-- hidden unless the team owner explicitly allows visibility or the viewer is a
-- higher-ranked role with manage_roles.
create table if not exists public.team_role_visibility (
    team_id uuid not null references public.teams(id) on delete cascade,
    viewer_role_id uuid not null references public.team_roles(id) on delete cascade,
    target_role_id uuid not null references public.team_roles(id) on delete cascade,
    can_view boolean not null default true,
    updated_at timestamptz not null default now(),
    primary key(team_id, viewer_role_id, target_role_id)
);

create table if not exists public.user_notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    event_type text not null,
    title text not null check (char_length(title) <= 300),
    detail text not null default '' check (char_length(detail) <= 4000),
    metadata jsonb not null default '{}'::jsonb,
    is_read boolean not null default false,
    created_at timestamptz not null default now()
);
create index if not exists user_notifications_user_unread_idx
    on public.user_notifications(user_id,is_read,created_at desc);

create table if not exists public.team_activity (
    id uuid primary key default gen_random_uuid(),
    team_id uuid not null references public.teams(id) on delete cascade,
    actor_id uuid references public.profiles(id) on delete set null,
    event_type text not null,
    title text not null check (char_length(title) <= 300),
    detail text not null default '' check (char_length(detail) <= 4000),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);
create index if not exists team_activity_team_created_idx on public.team_activity(team_id,created_at desc);

-- Permission JSON accepted by role-management RPCs is intentionally narrow.
-- Unknown keys or non-boolean values are rejected before they can reach role
-- evaluation (which also avoids malformed JSON causing authorization errors).
create or replace function public.devnest_permissions_valid(p_permissions jsonb)
returns boolean language sql immutable set search_path=public
as $$
    select jsonb_typeof(coalesce(p_permissions,'{}'::jsonb))='object'
       and not exists (
         select 1 from jsonb_each(coalesce(p_permissions,'{}'::jsonb)) e
         where e.key not in (
           'view_project','edit_project','delete_project','create_note','edit_note','delete_note',
           'create_decision','edit_decision','delete_decision','edit_architecture',
           'manage_access','manage_roles','invite_members'
         ) or jsonb_typeof(e.value)<>'boolean'
       )
$$;

-- ---------------------------------------------------------------------------
-- Security helper functions. They are SECURITY DEFINER so they can inspect
-- membership tables without RLS recursion. Every function pins search_path.
-- ---------------------------------------------------------------------------
create or replace function public.is_team_owner(p_team uuid, p_user uuid default auth.uid())
returns boolean language sql stable security definer set search_path=public
as $$ select exists(select 1 from public.teams t where t.id=p_team and t.owner_id=p_user) $$;

create or replace function public.is_team_member(p_team uuid, p_user uuid default auth.uid())
returns boolean language sql stable security definer set search_path=public
as $$
    select public.is_team_owner(p_team,p_user)
        or exists(select 1 from public.team_members m where m.team_id=p_team and m.user_id=p_user)
$$;

create or replace function public.team_user_rank(p_team uuid, p_user uuid default auth.uid())
returns integer language sql stable security definer set search_path=public
as $$
    select case
        when public.is_team_owner(p_team,p_user) then 1000000
        else coalesce((select r.rank from public.team_members m join public.team_roles r on r.id=m.role_id
                       where m.team_id=p_team and m.user_id=p_user),0)
    end
$$;

create or replace function public.team_has_permission(p_team uuid, p_user uuid, p_permission text)
returns boolean language plpgsql stable security definer set search_path=public
as $$
declare v_override boolean; v_role uuid; v_value boolean;
begin
    if public.is_team_owner(p_team,p_user) then return true; end if;
    select o.allow into v_override from public.team_member_permission_overrides o
      where o.team_id=p_team and o.user_id=p_user and o.permission_key=p_permission;
    if found then return v_override; end if;
    select m.role_id into v_role from public.team_members m where m.team_id=p_team and m.user_id=p_user;
    if v_role is null then return false; end if;
    select coalesce((r.permissions->>p_permission)::boolean,false) into v_value
      from public.team_roles r where r.id=v_role and r.team_id=p_team;
    return coalesce(v_value,false);
end;
$$;

create or replace function public.team_can_manage_member(p_team uuid, p_actor uuid, p_target uuid)
returns boolean language sql stable security definer set search_path=public
as $$
    select p_actor is not null and p_target is not null and p_actor<>p_target
       and not public.is_team_owner(p_team,p_target)
       and (
           public.is_team_owner(p_team,p_actor)
           or (public.team_has_permission(p_team,p_actor,'manage_roles')
               and public.team_user_rank(p_team,p_actor) > public.team_user_rank(p_team,p_target))
       )
$$;

create or replace function public.team_can_view_role(p_team uuid, p_role uuid, p_user uuid default auth.uid())
returns boolean language plpgsql stable security definer set search_path=public
as $$
declare v_own_role uuid; v_target_rank int;
begin
    if public.is_team_owner(p_team,p_user) then return true; end if;
    select role_id into v_own_role from public.team_members where team_id=p_team and user_id=p_user;
    if v_own_role is null then return false; end if;
    if v_own_role=p_role then return true; end if;
    if exists(select 1 from public.team_role_visibility v where v.team_id=p_team and v.viewer_role_id=v_own_role and v.target_role_id=p_role and v.can_view) then
        return true;
    end if;
    select rank into v_target_rank from public.team_roles where id=p_role and team_id=p_team;
    return public.team_has_permission(p_team,p_user,'manage_roles')
       and public.team_user_rank(p_team,p_user)>coalesce(v_target_rank,1000001);
end;
$$;

create or replace function public.team_can_view_member(p_team uuid, p_target uuid, p_user uuid default auth.uid())
returns boolean language plpgsql stable security definer set search_path=public
as $$
declare v_target_role uuid;
begin
    if p_user=p_target or public.is_team_owner(p_team,p_user) then return true; end if;
    if public.is_team_owner(p_team,p_target) then return public.is_team_member(p_team,p_user); end if;
    select role_id into v_target_role from public.team_members where team_id=p_team and user_id=p_target;
    if v_target_role is null then return false; end if;
    return public.team_can_view_role(p_team,v_target_role,p_user);
end;
$$;

create or replace function public.profile_visible_to(p_profile uuid, p_user uuid default auth.uid())
returns boolean language sql stable security definer set search_path=public
as $$
    select p_profile=p_user or exists(
        select 1 from public.teams t
        where public.is_team_member(t.id,p_user)
          and (t.owner_id=p_profile or exists(select 1 from public.team_members m where m.team_id=t.id and m.user_id=p_profile))
          and public.team_can_view_member(t.id,p_profile,p_user)
    )
$$;

create or replace function public.team_project_permission(p_project uuid, p_permission text, p_user uuid default auth.uid())
returns boolean language sql stable security definer set search_path=public
as $$
    select exists(
        select 1 from public.team_projects tp
        where tp.project_id=p_project
          and public.is_team_member(tp.team_id,p_user)
          and public.team_has_permission(tp.team_id,p_user,p_permission)
    )
$$;

create or replace function public.team_can_view_resource(
    p_project uuid, p_type text, p_key text, p_user uuid default auth.uid()
) returns boolean language plpgsql stable security definer set search_path=public
as $$
declare rec record; v_role uuid; v_restricted boolean;
begin
    for rec in select tp.team_id from public.team_projects tp where tp.project_id=p_project loop
        if not public.is_team_member(rec.team_id,p_user)
           or not public.team_has_permission(rec.team_id,p_user,'view_project') then
            continue;
        end if;
        select p.restricted into v_restricted from public.team_resource_policies p
         where p.team_id=rec.team_id and p.project_id=p_project and p.resource_type=p_type and p.resource_key=p_key;
        if not found or not v_restricted then return true; end if;
        if exists(select 1 from public.team_resource_acl a where a.team_id=rec.team_id and a.project_id=p_project
                  and a.resource_type=p_type and a.resource_key=p_key and a.can_view and a.subject_user_id=p_user) then
            return true;
        end if;
        select role_id into v_role from public.team_members where team_id=rec.team_id and user_id=p_user;
        if v_role is not null and exists(select 1 from public.team_resource_acl a where a.team_id=rec.team_id and a.project_id=p_project
                  and a.resource_type=p_type and a.resource_key=p_key and a.can_view and a.subject_role_id=v_role) then
            return true;
        end if;
    end loop;
    return false;
end;
$$;

create or replace function public.team_can_change_resource(
    p_project uuid, p_type text, p_key text, p_action text, p_user uuid default auth.uid()
) returns boolean language plpgsql stable security definer set search_path=public
as $$
declare rec record; v_permission text;
begin
    -- Repository membership is intentionally team-owner-only. This is stronger
    -- than a client-side disabled button and cannot be bypassed with raw REST.
    if p_type='repository' then
        return exists(select 1 from public.team_projects tp join public.teams t on t.id=tp.team_id
                      where tp.project_id=p_project and t.owner_id=p_user);
    end if;
    v_permission := case
        when p_type='note' and p_action='insert' then 'create_note'
        when p_type='note' and p_action='update' then 'edit_note'
        when p_type='note' and p_action='delete' then 'delete_note'
        when p_type='decision' and p_action='insert' then 'create_decision'
        when p_type='decision' and p_action='update' then 'edit_decision'
        when p_type='decision' and p_action='delete' then 'delete_decision'
        when p_type='architecture' then 'edit_architecture'
        else null end;
    if v_permission is null then return false; end if;
    for rec in select tp.team_id from public.team_projects tp where tp.project_id=p_project loop
        if public.team_has_permission(rec.team_id,p_user,v_permission)
           and (p_action='insert' or public.team_can_view_resource(p_project,p_type,p_key,p_user)) then
            return true;
        end if;
    end loop;
    return false;
end;
$$;

-- ---------------------------------------------------------------------------
-- RLS + grants. anon gets no table access. authenticated receives only the
-- operations used by the desktop client, then row policies narrow them.
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.cloud_projects enable row level security;
alter table public.cloud_resources enable row level security;
alter table public.teams enable row level security;
alter table public.team_roles enable row level security;
alter table public.team_members enable row level security;
alter table public.team_invitations enable row level security;
alter table public.team_projects enable row level security;
alter table public.team_member_permission_overrides enable row level security;
alter table public.team_resource_policies enable row level security;
alter table public.team_resource_acl enable row level security;
alter table public.team_role_visibility enable row level security;
alter table public.user_notifications enable row level security;
alter table public.team_activity enable row level security;

revoke all on public.profiles, public.cloud_projects, public.cloud_resources, public.teams,
    public.team_roles, public.team_members, public.team_invitations, public.team_projects,
    public.team_member_permission_overrides, public.team_resource_policies, public.team_resource_acl,
    public.team_role_visibility, public.user_notifications, public.team_activity from authenticated;

grant select, update on public.profiles to authenticated;
grant select, insert, update, delete on public.cloud_projects, public.cloud_resources to authenticated;
grant select on public.teams, public.team_roles, public.team_members, public.team_invitations, public.team_projects,
    public.team_member_permission_overrides, public.team_resource_policies, public.team_resource_acl,
    public.team_role_visibility to authenticated;
grant select, update on public.user_notifications to authenticated;
grant select on public.team_activity to authenticated;

-- Drop/recreate policies to make the script safely re-runnable.
do $$ declare r record; begin
  for r in select schemaname, tablename, policyname from pg_policies where schemaname='public' and tablename in
    ('profiles','cloud_projects','cloud_resources','teams','team_roles','team_members','team_invitations','team_projects',
     'team_member_permission_overrides','team_resource_policies','team_resource_acl','team_role_visibility','user_notifications','team_activity')
  loop execute format('drop policy if exists %I on public.%I',r.policyname,r.tablename); end loop;
end $$;

create policy profiles_select on public.profiles for select to authenticated
 using (public.profile_visible_to(id,(select auth.uid())));
create policy profiles_update_self on public.profiles for update to authenticated
 using (id=(select auth.uid())) with check (id=(select auth.uid()));

create policy cloud_projects_select on public.cloud_projects for select to authenticated
 using (owner_id=(select auth.uid()) or public.team_project_permission(id,'view_project',(select auth.uid())));
create policy cloud_projects_insert on public.cloud_projects for insert to authenticated
 with check (owner_id=(select auth.uid()));
create policy cloud_projects_update on public.cloud_projects for update to authenticated
 using (owner_id=(select auth.uid()) or public.team_project_permission(id,'edit_project',(select auth.uid())))
 with check (owner_id=(select auth.uid()) or public.team_project_permission(id,'edit_project',(select auth.uid())));
create policy cloud_projects_delete on public.cloud_projects for delete to authenticated
 using (owner_id=(select auth.uid()));

create policy cloud_resources_select on public.cloud_resources for select to authenticated
 using (owner_id=(select auth.uid()) or public.team_can_view_resource(project_id,resource_type,local_key,(select auth.uid())));
create policy cloud_resources_insert on public.cloud_resources for insert to authenticated
 with check (
   (owner_id=(select auth.uid()) and exists(select 1 from public.cloud_projects p where p.id=project_id and p.owner_id=(select auth.uid())))
   or public.team_can_change_resource(project_id,resource_type,local_key,'insert',(select auth.uid()))
 );
create policy cloud_resources_update on public.cloud_resources for update to authenticated
 using (owner_id=(select auth.uid()) or public.team_can_change_resource(project_id,resource_type,local_key,'update',(select auth.uid())))
 with check (owner_id=(select auth.uid()) or public.team_can_change_resource(project_id,resource_type,local_key,'update',(select auth.uid())));
create policy cloud_resources_delete on public.cloud_resources for delete to authenticated
 using (owner_id=(select auth.uid()) or public.team_can_change_resource(project_id,resource_type,local_key,'delete',(select auth.uid())));

create policy teams_select on public.teams for select to authenticated
 using (public.is_team_member(id,(select auth.uid())) or exists(select 1 from public.team_invitations i where i.team_id=id and i.invitee_id=(select auth.uid()) and i.status='pending'));
create policy team_roles_select on public.team_roles for select to authenticated
 using (public.team_can_view_role(team_id,id,(select auth.uid())));
create policy team_members_select on public.team_members for select to authenticated
 using (public.team_can_view_member(team_id,user_id,(select auth.uid())));
create policy team_invitations_select on public.team_invitations for select to authenticated
 using (invitee_id=(select auth.uid()) or public.is_team_owner(team_id,(select auth.uid())) or inviter_id=(select auth.uid()));
create policy team_projects_select on public.team_projects for select to authenticated
 using (public.is_team_member(team_id,(select auth.uid())));
create policy team_member_overrides_select on public.team_member_permission_overrides for select to authenticated
 using (user_id=(select auth.uid()) or public.is_team_owner(team_id,(select auth.uid())) or public.team_can_manage_member(team_id,(select auth.uid()),user_id));
create policy team_resource_policies_select on public.team_resource_policies for select to authenticated
 using (public.is_team_member(team_id,(select auth.uid())));
create policy team_resource_acl_select on public.team_resource_acl for select to authenticated
 using (public.is_team_owner(team_id,(select auth.uid())) or subject_user_id=(select auth.uid())
        or (subject_role_id is not null and public.team_can_view_role(team_id,subject_role_id,(select auth.uid())))
        or public.team_has_permission(team_id,(select auth.uid()),'manage_access'));
create policy team_role_visibility_select on public.team_role_visibility for select to authenticated
 using (public.is_team_owner(team_id,(select auth.uid())) or public.team_can_view_role(team_id,viewer_role_id,(select auth.uid())));
create policy notifications_select on public.user_notifications for select to authenticated using (user_id=(select auth.uid()));
create policy notifications_update on public.user_notifications for update to authenticated
 using (user_id=(select auth.uid())) with check (user_id=(select auth.uid()));
create policy team_activity_select on public.team_activity for select to authenticated
 using (public.is_team_member(team_id,(select auth.uid()))
        and (actor_id is null or public.team_can_view_member(team_id,actor_id,(select auth.uid()))));

-- ---------------------------------------------------------------------------
-- Mutating RPC functions. Sensitive team tables are read-only through REST;
-- all writes go through these hierarchy-aware functions.
-- ---------------------------------------------------------------------------
create or replace function public.team_create(p_name text)
returns uuid language plpgsql security definer set search_path=public
as $$
declare v_team uuid; v_user uuid := auth.uid();
begin
    if v_user is null then raise exception 'authentication required'; end if;
    p_name := trim(p_name);
    if char_length(p_name) not between 2 and 80 then raise exception 'invalid team name'; end if;
    insert into public.teams(owner_id,name) values(v_user,p_name) returning id into v_team;
    insert into public.team_roles(team_id,name,rank,permissions,is_system) values
      (v_team,'Admin',8000,'{"view_project":true,"edit_project":true,"delete_project":false,"create_note":true,"edit_note":true,"delete_note":true,"create_decision":true,"edit_decision":true,"delete_decision":true,"edit_architecture":true,"manage_access":true,"manage_roles":true,"invite_members":true}'::jsonb,true),
      (v_team,'Member',1000,'{"view_project":true,"edit_project":false,"delete_project":false,"create_note":true,"edit_note":true,"delete_note":false,"create_decision":true,"edit_decision":true,"delete_decision":false,"edit_architecture":true,"manage_access":false,"manage_roles":false,"invite_members":false}'::jsonb,true);
    insert into public.team_activity(team_id,actor_id,event_type,title,detail) values(v_team,v_user,'team_created','Team created',p_name);
    return v_team;
end;
$$;

create or replace function public.team_invite_username(p_team_id uuid, p_username text)
returns uuid language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_target uuid; v_invite uuid; v_team_name text;
begin
    if not (public.is_team_owner(p_team_id,v_actor) or public.team_has_permission(p_team_id,v_actor,'invite_members')) then
        raise exception 'not allowed to invite members';
    end if;
    select id into v_target from public.profiles where lower(username)=lower(trim(p_username));
    if v_target is null then raise exception 'username not found'; end if;
    if v_target=v_actor then raise exception 'cannot invite yourself'; end if;
    if public.is_team_member(p_team_id,v_target) then raise exception 'user is already a team member'; end if;
    insert into public.team_invitations(team_id,inviter_id,invitee_id,status,created_at,responded_at)
    values(p_team_id,v_actor,v_target,'pending',now(),null)
    on conflict(team_id,invitee_id) do update set inviter_id=excluded.inviter_id,status='pending',created_at=now(),responded_at=null
    returning id into v_invite;
    select name into v_team_name from public.teams where id=p_team_id;
    insert into public.user_notifications(user_id,event_type,title,detail,metadata)
      values(v_target,'team_invite','Team invitation',v_team_name,jsonb_build_object('team_id',p_team_id,'invitation_id',v_invite));
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_actor,'member_invited','Member invited',trim(p_username),jsonb_build_object('invitee_id',v_target));
    return v_invite;
end;
$$;

create or replace function public.team_respond_invitation(p_invitation_id uuid, p_accept boolean)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_user uuid:=auth.uid(); v_inv public.team_invitations%rowtype; v_default_role uuid; v_team_name text;
begin
    select * into v_inv from public.team_invitations where id=p_invitation_id and invitee_id=v_user and status='pending' for update;
    if not found then raise exception 'pending invitation not found'; end if;
    if p_accept then
        select id into v_default_role from public.team_roles where team_id=v_inv.team_id order by rank asc limit 1;
        insert into public.team_members(team_id,user_id,role_id) values(v_inv.team_id,v_user,v_default_role)
        on conflict(team_id,user_id) do update set role_id=coalesce(public.team_members.role_id,excluded.role_id);
        update public.team_invitations set status='accepted',responded_at=now() where id=p_invitation_id;
    else
        update public.team_invitations set status='declined',responded_at=now() where id=p_invitation_id;
    end if;
    select name into v_team_name from public.teams where id=v_inv.team_id;
    insert into public.user_notifications(user_id,event_type,title,detail,metadata)
      select owner_id,'team_invite_response','Team invitation response',
             coalesce((select username from public.profiles where id=v_user),'member') || case when p_accept then ' accepted ' else ' declined ' end || v_team_name,
             jsonb_build_object('team_id',v_inv.team_id,'user_id',v_user,'accepted',p_accept)
      from public.teams where id=v_inv.team_id;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail)
      values(v_inv.team_id,v_user,case when p_accept then 'invite_accepted' else 'invite_declined' end,
             case when p_accept then 'Invitation accepted' else 'Invitation declined' end,'');
    return p_accept;
end;
$$;

create or replace function public.team_create_role(p_team_id uuid, p_name text, p_rank integer, p_permissions jsonb)
returns uuid language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_role uuid;
begin
    if not (public.is_team_owner(p_team_id,v_actor) or public.team_has_permission(p_team_id,v_actor,'manage_roles')) then raise exception 'not allowed'; end if;
    if p_rank<1 or p_rank>=public.team_user_rank(p_team_id,v_actor) then raise exception 'role rank must be below your own rank'; end if;
    if char_length(trim(p_name)) not between 1 and 80 then raise exception 'invalid role name'; end if;
    if not public.devnest_permissions_valid(p_permissions) then raise exception 'invalid role permissions'; end if;
    insert into public.team_roles(team_id,name,rank,permissions) values(p_team_id,trim(p_name),p_rank,coalesce(p_permissions,'{}'::jsonb)) returning id into v_role;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_actor,'role_created','Role created',trim(p_name),jsonb_build_object('role_id',v_role,'rank',p_rank));
    return v_role;
end;
$$;

create or replace function public.team_update_role(p_role_id uuid, p_name text, p_rank integer, p_permissions jsonb)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_role public.team_roles%rowtype; v_actor_rank int;
begin
    select * into v_role from public.team_roles where id=p_role_id for update;
    if not found then raise exception 'role not found'; end if;
    v_actor_rank:=public.team_user_rank(v_role.team_id,v_actor);
    if not (public.is_team_owner(v_role.team_id,v_actor) or public.team_has_permission(v_role.team_id,v_actor,'manage_roles')) then raise exception 'not allowed'; end if;
    if v_role.rank>=v_actor_rank or p_rank>=v_actor_rank or p_rank<1 then raise exception 'cannot edit your own, equal, or higher role'; end if;
    if char_length(trim(p_name)) not between 1 and 80 then raise exception 'invalid role name'; end if;
    if not public.devnest_permissions_valid(p_permissions) then raise exception 'invalid role permissions'; end if;
    if v_role.is_system and not public.is_team_owner(v_role.team_id,v_actor) then raise exception 'only owner can edit system roles'; end if;
    update public.team_roles set name=trim(p_name),rank=p_rank,permissions=coalesce(p_permissions,'{}'::jsonb),updated_at=now() where id=p_role_id;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(v_role.team_id,v_actor,'role_updated','Role updated',trim(p_name),jsonb_build_object('role_id',p_role_id,'rank',p_rank));
    return true;
end;
$$;

create or replace function public.team_assign_role(p_team_id uuid, p_user_id uuid, p_role_id uuid)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_role_rank int;
begin
    if not public.team_can_manage_member(p_team_id,v_actor,p_user_id) then raise exception 'cannot manage this member'; end if;
    select rank into v_role_rank from public.team_roles where id=p_role_id and team_id=p_team_id;
    if v_role_rank is null then raise exception 'role not found'; end if;
    if v_role_rank>=public.team_user_rank(p_team_id,v_actor) then raise exception 'cannot assign an equal or higher role'; end if;
    update public.team_members set role_id=p_role_id where team_id=p_team_id and user_id=p_user_id;
    if not found then raise exception 'member not found'; end if;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_actor,'role_assigned','Role assigned','',jsonb_build_object('user_id',p_user_id,'role_id',p_role_id));
    return true;
end;
$$;

create or replace function public.team_set_member_permission(p_team_id uuid, p_user_id uuid, p_permission text, p_allow boolean)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid();
begin
    if p_permission not in ('view_project','edit_project','delete_project','create_note','edit_note','delete_note','create_decision','edit_decision','delete_decision','edit_architecture','manage_access','manage_roles','invite_members') then
       raise exception 'unknown permission';
    end if;
    if not public.team_can_manage_member(p_team_id,v_actor,p_user_id) then raise exception 'cannot manage this member'; end if;
    if p_allow is null then
      delete from public.team_member_permission_overrides where team_id=p_team_id and user_id=p_user_id and permission_key=p_permission;
    else
      insert into public.team_member_permission_overrides(team_id,user_id,permission_key,allow,updated_at)
      values(p_team_id,p_user_id,p_permission,p_allow,now())
      on conflict(team_id,user_id,permission_key) do update set allow=excluded.allow,updated_at=now();
    end if;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_actor,'member_permission_changed','Member permission changed',p_permission,
             jsonb_build_object('user_id',p_user_id,'allow',p_allow));
    return true;
end;
$$;

create or replace function public.team_assign_project(p_team_id uuid, p_project_id uuid)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_user uuid:=auth.uid();
begin
    if not public.is_team_owner(p_team_id,v_user) then raise exception 'only the team owner can assign projects'; end if;
    if not exists(select 1 from public.cloud_projects where id=p_project_id and owner_id=v_user) then
      raise exception 'the team owner can only assign a cloud project they own';
    end if;
    insert into public.team_projects(team_id,project_id,assigned_by) values(p_team_id,p_project_id,v_user)
      on conflict(team_id,project_id) do nothing;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_user,'project_assigned','Project assigned','',jsonb_build_object('project_id',p_project_id));
    return true;
end;
$$;

create or replace function public.team_unassign_project(p_team_id uuid, p_project_id uuid)
returns boolean language plpgsql security definer set search_path=public
as $$
begin
    if not public.is_team_owner(p_team_id,auth.uid()) then raise exception 'only the team owner can remove projects'; end if;
    delete from public.team_projects where team_id=p_team_id and project_id=p_project_id;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,auth.uid(),'project_unassigned','Project unassigned','',jsonb_build_object('project_id',p_project_id));
    return true;
end;
$$;

create or replace function public.team_replace_resource_user_acl(
    p_team_id uuid, p_project_id uuid, p_resource_type text, p_resource_key text,
    p_allowed_users uuid[], p_restricted boolean default true
) returns boolean language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_user uuid;
begin
    if p_resource_type not in ('note','decision','architecture') then raise exception 'unsupported private resource type'; end if;
    if char_length(p_resource_key) not between 1 and 160 then raise exception 'invalid resource key'; end if;
    if coalesce(array_length(p_allowed_users,1),0) > 500 then raise exception 'too many ACL users'; end if;
    if not exists(select 1 from public.team_projects where team_id=p_team_id and project_id=p_project_id) then raise exception 'project is not assigned to this team'; end if;
    if not public.is_team_owner(p_team_id,v_actor) then
      if not public.team_has_permission(p_team_id,v_actor,'manage_access') then raise exception 'not allowed to manage resource access'; end if;
      -- A delegated access manager cannot guess the key of a private resource
      -- they themselves are excluded from and then make it public.
      if exists(select 1 from public.team_resource_policies p
                where p.team_id=p_team_id and p.project_id=p_project_id and p.resource_type=p_resource_type
                  and p.resource_key=p_resource_key and p.restricted)
         and not (
           exists(select 1 from public.team_resource_acl a
                  where a.team_id=p_team_id and a.project_id=p_project_id and a.resource_type=p_resource_type
                    and a.resource_key=p_resource_key and a.can_view and a.subject_user_id=v_actor)
           or exists(select 1 from public.team_resource_acl a join public.team_members m
                     on m.team_id=p_team_id and m.user_id=v_actor and m.role_id=a.subject_role_id
                     where a.team_id=p_team_id and a.project_id=p_project_id and a.resource_type=p_resource_type
                       and a.resource_key=p_resource_key and a.can_view)
         ) then
        raise exception 'cannot manage a private resource you cannot view';
      end if;
    end if;
    insert into public.team_resource_policies(team_id,project_id,resource_type,resource_key,restricted,updated_at)
      values(p_team_id,p_project_id,p_resource_type,p_resource_key,p_restricted,now())
      on conflict(team_id,project_id,resource_type,resource_key) do update set restricted=excluded.restricted,updated_at=now();
    delete from public.team_resource_acl where team_id=p_team_id and project_id=p_project_id and resource_type=p_resource_type and resource_key=p_resource_key and subject_user_id is not null;
    if p_restricted then
      foreach v_user in array coalesce(p_allowed_users,array[]::uuid[]) loop
        if not public.is_team_member(p_team_id,v_user) then raise exception 'ACL target is not a team member'; end if;
        if not public.is_team_owner(p_team_id,v_actor) and not public.team_can_manage_member(p_team_id,v_actor,v_user) and v_user<>v_actor then
          raise exception 'cannot change access for equal or higher member';
        end if;
        insert into public.team_resource_acl(team_id,project_id,resource_type,resource_key,subject_user_id,can_view)
          values(p_team_id,p_project_id,p_resource_type,p_resource_key,v_user,true)
          on conflict do nothing;
      end loop;
    end if;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_actor,'resource_access_changed','Resource access changed',p_resource_type || ':' || p_resource_key,
             jsonb_build_object('project_id',p_project_id,'restricted',p_restricted));
    return true;
end;
$$;

create or replace function public.team_replace_role_visibility(p_team_id uuid, p_viewer_role_id uuid, p_target_role_ids uuid[])
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_target uuid;
begin
    if not public.is_team_owner(p_team_id,auth.uid()) then raise exception 'only the team owner can configure department visibility'; end if;
    if coalesce(array_length(p_target_role_ids,1),0) > 250 then raise exception 'too many target roles'; end if;
    if not exists(select 1 from public.team_roles where id=p_viewer_role_id and team_id=p_team_id) then raise exception 'viewer role not found'; end if;
    delete from public.team_role_visibility where team_id=p_team_id and viewer_role_id=p_viewer_role_id;
    foreach v_target in array coalesce(p_target_role_ids,array[]::uuid[]) loop
      if not exists(select 1 from public.team_roles where id=v_target and team_id=p_team_id) then raise exception 'target role not found'; end if;
      if v_target<>p_viewer_role_id then
        insert into public.team_role_visibility(team_id,viewer_role_id,target_role_id,can_view)
          values(p_team_id,p_viewer_role_id,v_target,true) on conflict do nothing;
      end if;
    end loop;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,auth.uid(),'role_visibility_changed','Role visibility changed','',jsonb_build_object('viewer_role_id',p_viewer_role_id));
    return true;
end;
$$;

-- Trigger-only/validation helpers are not part of the client RPC surface.
revoke all on function public.guard_devnest_cloud_project_identity() from public, anon, authenticated;
revoke all on function public.guard_devnest_cloud_resource_identity() from public, anon, authenticated;
revoke all on function public.devnest_permissions_valid(jsonb) from public, anon, authenticated;

-- Helper functions are callable by RLS but not by signed-out clients. They
-- intentionally reveal only authorization booleans, never protected rows.
revoke all on function public.is_team_owner(uuid,uuid) from public, anon;
revoke all on function public.is_team_member(uuid,uuid) from public, anon;
revoke all on function public.team_user_rank(uuid,uuid) from public, anon;
revoke all on function public.team_has_permission(uuid,uuid,text) from public, anon;
revoke all on function public.team_can_manage_member(uuid,uuid,uuid) from public, anon;
revoke all on function public.team_can_view_role(uuid,uuid,uuid) from public, anon;
revoke all on function public.team_can_view_member(uuid,uuid,uuid) from public, anon;
revoke all on function public.profile_visible_to(uuid,uuid) from public, anon;
revoke all on function public.team_project_permission(uuid,text,uuid) from public, anon;
revoke all on function public.team_can_view_resource(uuid,text,text,uuid) from public, anon;
revoke all on function public.team_can_change_resource(uuid,text,text,text,uuid) from public, anon;
grant execute on function public.is_team_owner(uuid,uuid), public.is_team_member(uuid,uuid), public.team_user_rank(uuid,uuid),
 public.team_has_permission(uuid,uuid,text), public.team_can_manage_member(uuid,uuid,uuid),
 public.team_can_view_role(uuid,uuid,uuid), public.team_can_view_member(uuid,uuid,uuid),
 public.profile_visible_to(uuid,uuid), public.team_project_permission(uuid,text,uuid),
 public.team_can_view_resource(uuid,text,text,uuid), public.team_can_change_resource(uuid,text,text,text,uuid) to authenticated;

-- Explicitly expose only the intended RPC surface to signed-in users.
revoke all on function public.team_create(text) from public, anon;
revoke all on function public.team_invite_username(uuid,text) from public, anon;
revoke all on function public.team_respond_invitation(uuid,boolean) from public, anon;
revoke all on function public.team_create_role(uuid,text,integer,jsonb) from public, anon;
revoke all on function public.team_update_role(uuid,text,integer,jsonb) from public, anon;
revoke all on function public.team_assign_role(uuid,uuid,uuid) from public, anon;
revoke all on function public.team_set_member_permission(uuid,uuid,text,boolean) from public, anon;
revoke all on function public.team_assign_project(uuid,uuid) from public, anon;
revoke all on function public.team_unassign_project(uuid,uuid) from public, anon;
revoke all on function public.team_replace_resource_user_acl(uuid,uuid,text,text,uuid[],boolean) from public, anon;
revoke all on function public.team_replace_role_visibility(uuid,uuid,uuid[]) from public, anon;

grant execute on function public.team_create(text) to authenticated;
grant execute on function public.team_invite_username(uuid,text) to authenticated;
grant execute on function public.team_respond_invitation(uuid,boolean) to authenticated;
grant execute on function public.team_create_role(uuid,text,integer,jsonb) to authenticated;
grant execute on function public.team_update_role(uuid,text,integer,jsonb) to authenticated;
grant execute on function public.team_assign_role(uuid,uuid,uuid) to authenticated;
grant execute on function public.team_set_member_permission(uuid,uuid,text,boolean) to authenticated;
grant execute on function public.team_assign_project(uuid,uuid) to authenticated;
grant execute on function public.team_unassign_project(uuid,uuid) to authenticated;
grant execute on function public.team_replace_resource_user_acl(uuid,uuid,text,text,uuid[],boolean) to authenticated;
grant execute on function public.team_replace_role_visibility(uuid,uuid,uuid[]) to authenticated;

-- ---------------------------------------------------------------------------
-- DevNest Online v2: manual backup revisions, automatic role hierarchy and
-- low-latency team snapshots. This section is intentionally idempotent so an
-- existing Supabase project can run the entire schema file again as a migration.
-- ---------------------------------------------------------------------------

alter table public.cloud_projects add column if not exists revision bigint not null default 1;
alter table public.cloud_projects add column if not exists updated_by uuid references public.profiles(id) on delete set null;
alter table public.cloud_resources add column if not exists revision bigint not null default 1;
alter table public.cloud_resources add column if not exists updated_by uuid references public.profiles(id) on delete set null;

create or replace function public.devnest_touch_cloud_revision()
returns trigger
language plpgsql
set search_path=public
as $$
begin
    if tg_op='INSERT' then
        new.revision := greatest(1,coalesce(new.revision,1));
    else
        new.revision := greatest(1,coalesce(old.revision,1)) + 1;
    end if;
    new.updated_at := now();
    new.updated_by := auth.uid();
    return new;
end;
$$;

drop trigger if exists devnest_cloud_project_revision on public.cloud_projects;
create trigger devnest_cloud_project_revision
before insert or update on public.cloud_projects
for each row execute function public.devnest_touch_cloud_revision();

drop trigger if exists devnest_cloud_resource_revision on public.cloud_resources;
create trigger devnest_cloud_resource_revision
before insert or update on public.cloud_resources
for each row execute function public.devnest_touch_cloud_revision();

-- Rank remains an internal server-side value because hierarchy comparisons are
-- efficient with an integer. Users never enter or edit it. Permission weights
-- are deterministic, and stronger destructive/administrative capabilities
-- contribute more than ordinary read/write capabilities.
create or replace function public.devnest_permission_rank(p_permissions jsonb)
returns integer
language sql
immutable
set search_path=public
as $$
    select 100
      + case when coalesce((p_permissions->>'view_project')::boolean,false) then 10 else 0 end
      + case when coalesce((p_permissions->>'create_note')::boolean,false) then 20 else 0 end
      + case when coalesce((p_permissions->>'edit_note')::boolean,false) then 35 else 0 end
      + case when coalesce((p_permissions->>'delete_note')::boolean,false) then 90 else 0 end
      + case when coalesce((p_permissions->>'create_decision')::boolean,false) then 20 else 0 end
      + case when coalesce((p_permissions->>'edit_decision')::boolean,false) then 35 else 0 end
      + case when coalesce((p_permissions->>'delete_decision')::boolean,false) then 90 else 0 end
      + case when coalesce((p_permissions->>'edit_architecture')::boolean,false) then 45 else 0 end
      + case when coalesce((p_permissions->>'edit_project')::boolean,false) then 120 else 0 end
      + case when coalesce((p_permissions->>'manage_access')::boolean,false) then 180 else 0 end
      + case when coalesce((p_permissions->>'invite_members')::boolean,false) then 220 else 0 end
      + case when coalesce((p_permissions->>'manage_roles')::boolean,false) then 450 else 0 end
      + case when coalesce((p_permissions->>'delete_project')::boolean,false) then 600 else 0 end
$$;

-- Personal allow/deny overrides also affect the effective hierarchy. This keeps
-- a member who was explicitly granted administrative powers from being treated
-- as a low-level role only because the base role is small.
create or replace function public.team_user_rank(p_team uuid, p_user uuid default auth.uid())
returns integer
language sql
stable
security definer
set search_path=public
as $$
    select case
      when public.is_team_owner(p_team,p_user) then 1000000
      when not exists(select 1 from public.team_members m where m.team_id=p_team and m.user_id=p_user) then 0
      else public.devnest_permission_rank(jsonb_build_object(
        'view_project',public.team_has_permission(p_team,p_user,'view_project'),
        'edit_project',public.team_has_permission(p_team,p_user,'edit_project'),
        'delete_project',public.team_has_permission(p_team,p_user,'delete_project'),
        'create_note',public.team_has_permission(p_team,p_user,'create_note'),
        'edit_note',public.team_has_permission(p_team,p_user,'edit_note'),
        'delete_note',public.team_has_permission(p_team,p_user,'delete_note'),
        'create_decision',public.team_has_permission(p_team,p_user,'create_decision'),
        'edit_decision',public.team_has_permission(p_team,p_user,'edit_decision'),
        'delete_decision',public.team_has_permission(p_team,p_user,'delete_decision'),
        'edit_architecture',public.team_has_permission(p_team,p_user,'edit_architecture'),
        'manage_access',public.team_has_permission(p_team,p_user,'manage_access'),
        'manage_roles',public.team_has_permission(p_team,p_user,'manage_roles'),
        'invite_members',public.team_has_permission(p_team,p_user,'invite_members')
      ))
    end
$$;

-- Recalculate pre-v2 roles. Duplicate ranks are intentionally allowed; equal
-- effective permission sets are equal in hierarchy.
update public.team_roles
set rank=public.devnest_permission_rank(permissions),updated_at=now()
where rank is distinct from public.devnest_permission_rank(permissions);

-- Replace team creation so built-in role ranks are also derived, not hard-coded.
create or replace function public.team_create(p_name text)
returns uuid language plpgsql security definer set search_path=public
as $$
declare
    v_team uuid;
    v_user uuid := auth.uid();
    v_admin jsonb := '{"view_project":true,"edit_project":true,"delete_project":false,"create_note":true,"edit_note":true,"delete_note":true,"create_decision":true,"edit_decision":true,"delete_decision":true,"edit_architecture":true,"manage_access":true,"manage_roles":true,"invite_members":true}'::jsonb;
    v_member jsonb := '{"view_project":true,"edit_project":false,"delete_project":false,"create_note":true,"edit_note":true,"delete_note":false,"create_decision":true,"edit_decision":true,"delete_decision":false,"edit_architecture":true,"manage_access":false,"manage_roles":false,"invite_members":false}'::jsonb;
begin
    if v_user is null then raise exception 'authentication required'; end if;
    p_name := trim(p_name);
    if char_length(p_name) not between 2 and 80 then raise exception 'invalid team name'; end if;
    insert into public.teams(owner_id,name) values(v_user,p_name) returning id into v_team;
    insert into public.team_roles(team_id,name,rank,permissions,is_system) values
      (v_team,'Admin',public.devnest_permission_rank(v_admin),v_admin,true),
      (v_team,'Member',public.devnest_permission_rank(v_member),v_member,true);
    insert into public.team_activity(team_id,actor_id,event_type,title,detail)
      values(v_team,v_user,'team_created','Team created',p_name);
    return v_team;
end;
$$;

-- Old clients could submit an arbitrary rank. Remove that RPC surface entirely.
drop function if exists public.team_create_role(uuid,text,integer,jsonb);
drop function if exists public.team_update_role(uuid,text,integer,jsonb);

create or replace function public.team_create_role(p_team_id uuid, p_name text, p_permissions jsonb)
returns uuid language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_role uuid; v_rank integer;
begin
    if not (public.is_team_owner(p_team_id,v_actor) or public.team_has_permission(p_team_id,v_actor,'manage_roles')) then
        raise exception 'not allowed';
    end if;
    if char_length(trim(p_name)) not between 1 and 80 then raise exception 'invalid role name'; end if;
    if not public.devnest_permissions_valid(p_permissions) then raise exception 'invalid role permissions'; end if;
    v_rank := public.devnest_permission_rank(coalesce(p_permissions,'{}'::jsonb));
    if not public.is_team_owner(p_team_id,v_actor) and v_rank>=public.team_user_rank(p_team_id,v_actor) then
        raise exception 'cannot create an equal or higher role';
    end if;
    insert into public.team_roles(team_id,name,rank,permissions)
      values(p_team_id,trim(p_name),v_rank,coalesce(p_permissions,'{}'::jsonb))
      returning id into v_role;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_actor,'role_created','Role created',trim(p_name),
             jsonb_build_object('role_id',v_role,'derived_rank',v_rank));
    return v_role;
end;
$$;

create or replace function public.team_update_role(p_role_id uuid, p_name text, p_permissions jsonb)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_role public.team_roles%rowtype; v_actor_rank int; v_new_rank int;
begin
    select * into v_role from public.team_roles where id=p_role_id for update;
    if not found then raise exception 'role not found'; end if;
    v_actor_rank:=public.team_user_rank(v_role.team_id,v_actor);
    if not (public.is_team_owner(v_role.team_id,v_actor) or public.team_has_permission(v_role.team_id,v_actor,'manage_roles')) then
        raise exception 'not allowed';
    end if;
    if v_role.rank>=v_actor_rank then raise exception 'cannot edit your own, equal, or higher role'; end if;
    if char_length(trim(p_name)) not between 1 and 80 then raise exception 'invalid role name'; end if;
    if not public.devnest_permissions_valid(p_permissions) then raise exception 'invalid role permissions'; end if;
    if v_role.is_system and not public.is_team_owner(v_role.team_id,v_actor) then raise exception 'only owner can edit system roles'; end if;
    v_new_rank := public.devnest_permission_rank(coalesce(p_permissions,'{}'::jsonb));
    if not public.is_team_owner(v_role.team_id,v_actor) and v_new_rank>=v_actor_rank then
        raise exception 'cannot promote a role to your own or a higher level';
    end if;
    update public.team_roles
      set name=trim(p_name),rank=v_new_rank,permissions=coalesce(p_permissions,'{}'::jsonb),updated_at=now()
      where id=p_role_id;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(v_role.team_id,v_actor,'role_updated','Role updated',trim(p_name),
             jsonb_build_object('role_id',p_role_id,'derived_rank',v_new_rank));
    return true;
end;
$$;

-- One RPC replaces the two sequential requests previously made every time the
-- Teams page opened. It includes pending-team names so the UI needs no follow-up.
create or replace function public.team_overview()
returns jsonb language plpgsql stable security definer set search_path=public
as $$
declare v_user uuid:=auth.uid(); v_teams jsonb; v_invites jsonb;
begin
    if v_user is null then raise exception 'authentication required'; end if;
    select coalesce(jsonb_agg(jsonb_build_object(
        'id',t.id,'name',t.name,'owner_id',t.owner_id,'created_at',t.created_at,'updated_at',t.updated_at
      ) order by t.created_at desc),'[]'::jsonb)
      into v_teams
      from public.teams t
      where public.is_team_member(t.id,v_user)
         or exists(select 1 from public.team_invitations i
                   where i.team_id=t.id and i.invitee_id=v_user and i.status='pending');

    select coalesce(jsonb_agg(jsonb_build_object(
        'id',i.id,'team_id',i.team_id,'team_name',t.name,'inviter_id',i.inviter_id,
        'invitee_id',i.invitee_id,'status',i.status,'created_at',i.created_at
      ) order by i.created_at desc),'[]'::jsonb)
      into v_invites
      from public.team_invitations i join public.teams t on t.id=i.team_id
      where i.invitee_id=v_user and i.status='pending';

    return jsonb_build_object('teams',v_teams,'invitations',v_invites);
end;
$$;

-- A single detail snapshot replaces project + member + profile + role + activity
-- round-trips. Visibility helpers are still applied explicitly even though this
-- is SECURITY DEFINER, so department/private hierarchy boundaries are preserved.
create or replace function public.team_detail_snapshot(p_team_id uuid)
returns jsonb language plpgsql stable security definer set search_path=public
as $$
declare
    v_user uuid:=auth.uid();
    v_owner uuid;
    v_projects jsonb;
    v_members jsonb;
    v_roles jsonb;
    v_activity jsonb;
    v_viewer jsonb;
begin
    if v_user is null or not public.is_team_member(p_team_id,v_user) then
        raise exception 'team membership required';
    end if;
    select owner_id into v_owner from public.teams where id=p_team_id;
    if v_owner is null then raise exception 'team not found'; end if;

    v_viewer := jsonb_build_object(
      'user_id',v_user,
      'is_owner',public.is_team_owner(p_team_id,v_user),
      'role_id',(select m.role_id from public.team_members m where m.team_id=p_team_id and m.user_id=v_user),
      'rank',public.team_user_rank(p_team_id,v_user),
      'permissions',public.devnest_effective_permissions(p_team_id,v_user)
    );

    select coalesce(jsonb_agg(jsonb_build_object(
        'id',p.id,'name',p.name,'description',p.description,'owner_id',p.owner_id,
        'updated_at',p.updated_at,'updated_by',p.updated_by,'revision',p.revision,
        'assigned_at',tp.assigned_at
      ) order by tp.assigned_at desc),'[]'::jsonb)
      into v_projects
      from public.team_projects tp join public.cloud_projects p on p.id=tp.project_id
      where tp.team_id=p_team_id and public.team_project_permission(p.id,'view_project',v_user);

    select coalesce(jsonb_agg(x.obj order by x.sort_key),'[]'::jsonb)
      into v_members
      from (
        select 0 as sort_key, jsonb_build_object(
          'team_id',p_team_id,'user_id',v_owner,'role_id',null,'joined_at',null,'is_owner',true,
          'profile',jsonb_build_object('id',p.id,'username',p.username,'first_name',p.first_name,'last_name',p.last_name),
          'role',jsonb_build_object('name','Owner','rank',1000000,'permissions','{}'::jsonb),
          'effective_permissions',public.devnest_effective_permissions(p_team_id,v_owner),
          'effective_rank',public.team_user_rank(p_team_id,v_owner)
        ) as obj
        from public.profiles p where p.id=v_owner
        union all
        select 1, jsonb_build_object(
          'team_id',m.team_id,'user_id',m.user_id,'role_id',m.role_id,'joined_at',m.joined_at,'is_owner',false,
          'profile',jsonb_build_object('id',p.id,'username',p.username,'first_name',p.first_name,'last_name',p.last_name),
          'role',case when r.id is null then '{}'::jsonb else jsonb_build_object(
            'id',r.id,'name',r.name,'rank',r.rank,'permissions',r.permissions,'is_system',r.is_system) end,
          'effective_permissions',public.devnest_effective_permissions(p_team_id,m.user_id),
          'effective_rank',public.team_user_rank(p_team_id,m.user_id)
        )
        from public.team_members m
        join public.profiles p on p.id=m.user_id
        left join public.team_roles r on r.id=m.role_id
        where m.team_id=p_team_id and public.team_can_view_member(p_team_id,m.user_id,v_user)
      ) x;

    select coalesce(jsonb_agg(jsonb_build_object(
        'id',r.id,'team_id',r.team_id,'name',r.name,'rank',r.rank,'permissions',r.permissions,
        'is_system',r.is_system,'created_at',r.created_at,'updated_at',r.updated_at
      ) order by r.rank desc,r.name),'[]'::jsonb)
      into v_roles
      from public.team_roles r
      where r.team_id=p_team_id and public.team_can_view_role(p_team_id,r.id,v_user);

    select coalesce(jsonb_agg(jsonb_build_object(
        'id',a.id,'team_id',a.team_id,'actor_id',a.actor_id,'event_type',a.event_type,
        'title',a.title,'detail',a.detail,'metadata',a.metadata,'created_at',a.created_at,
        'actor',case when p.id is null then '{}'::jsonb else jsonb_build_object(
          'id',p.id,'username',p.username,'first_name',p.first_name,'last_name',p.last_name) end
      ) order by a.created_at desc),'[]'::jsonb)
      into v_activity
      from (
        select * from public.team_activity a0
        where a0.team_id=p_team_id
          and (a0.actor_id is null or public.team_can_view_member(p_team_id,a0.actor_id,v_user))
        order by a0.created_at desc limit 200
      ) a
      left join public.profiles p on p.id=a.actor_id;

    return jsonb_build_object(
      'projects',v_projects,'members',v_members,'roles',v_roles,'activity',v_activity,'viewer',v_viewer
    );
end;
$$;

-- Trigger helper is not a public API.
revoke all on function public.devnest_touch_cloud_revision() from public,anon,authenticated;
revoke all on function public.devnest_permission_rank(jsonb) from public,anon,authenticated;

-- Replace the role RPC grants with the rank-free signatures.
revoke all on function public.team_create_role(uuid,text,jsonb) from public,anon;
revoke all on function public.team_update_role(uuid,text,jsonb) from public,anon;
grant execute on function public.team_create_role(uuid,text,jsonb) to authenticated;
grant execute on function public.team_update_role(uuid,text,jsonb) to authenticated;

revoke all on function public.team_overview() from public,anon;
revoke all on function public.team_detail_snapshot(uuid) from public,anon;
grant execute on function public.team_overview() to authenticated;
grant execute on function public.team_detail_snapshot(uuid) to authenticated;



-- ---------------------------------------------------------------------------
-- Live role hierarchy hardening (v3)
-- ---------------------------------------------------------------------------
-- Hierarchy is a permission partial-order, not merely a weighted number.  A
-- member with manage_roles can only manage a target whose effective permission
-- set is a *strict subset* of their own.  This prevents a low/custom role from
-- editing Admin just because a numeric score happened to be larger.
create or replace function public.devnest_effective_permissions(p_team uuid, p_user uuid)
returns jsonb
language sql
stable
security definer
set search_path=public
as $$
    select jsonb_build_object(
      'view_project',public.team_has_permission(p_team,p_user,'view_project'),
      'edit_project',public.team_has_permission(p_team,p_user,'edit_project'),
      'delete_project',public.team_has_permission(p_team,p_user,'delete_project'),
      'create_note',public.team_has_permission(p_team,p_user,'create_note'),
      'edit_note',public.team_has_permission(p_team,p_user,'edit_note'),
      'delete_note',public.team_has_permission(p_team,p_user,'delete_note'),
      'create_decision',public.team_has_permission(p_team,p_user,'create_decision'),
      'edit_decision',public.team_has_permission(p_team,p_user,'edit_decision'),
      'delete_decision',public.team_has_permission(p_team,p_user,'delete_decision'),
      'edit_architecture',public.team_has_permission(p_team,p_user,'edit_architecture'),
      'manage_access',public.team_has_permission(p_team,p_user,'manage_access'),
      'manage_roles',public.team_has_permission(p_team,p_user,'manage_roles'),
      'invite_members',public.team_has_permission(p_team,p_user,'invite_members')
    )
$$;

create or replace function public.devnest_permissions_strictly_dominate(p_actor jsonb, p_target jsonb)
returns boolean
language sql
immutable
set search_path=public
as $$
    with keys(k) as (values
      ('view_project'),('edit_project'),('delete_project'),('create_note'),('edit_note'),('delete_note'),
      ('create_decision'),('edit_decision'),('delete_decision'),('edit_architecture'),
      ('manage_access'),('manage_roles'),('invite_members')
    )
    select
      not exists (
        select 1 from keys
        where coalesce((p_target->>k)::boolean,false)
          and not coalesce((p_actor->>k)::boolean,false)
      )
      and exists (
        select 1 from keys
        where coalesce((p_actor->>k)::boolean,false)
          and not coalesce((p_target->>k)::boolean,false)
      )
$$;

create or replace function public.team_user_rank(p_team uuid, p_user uuid default auth.uid())
returns integer
language sql
stable
security definer
set search_path=public
as $$
    select case
      when public.is_team_owner(p_team,p_user) then 1000000
      when not exists(select 1 from public.team_members m where m.team_id=p_team and m.user_id=p_user) then 0
      else public.devnest_permission_rank(public.devnest_effective_permissions(p_team,p_user))
    end
$$;

create or replace function public.team_can_manage_member(p_team uuid, p_actor uuid, p_target uuid)
returns boolean
language sql
stable
security definer
set search_path=public
as $$
    select p_actor is not null and p_target is not null and p_actor<>p_target
       and not public.is_team_owner(p_team,p_target)
       and (
         public.is_team_owner(p_team,p_actor)
         or (
           public.team_has_permission(p_team,p_actor,'manage_roles')
           and public.devnest_permissions_strictly_dominate(
             public.devnest_effective_permissions(p_team,p_actor),
             public.devnest_effective_permissions(p_team,p_target)
           )
         )
       )
$$;

create or replace function public.team_can_manage_role(p_team uuid, p_actor uuid, p_role uuid)
returns boolean
language plpgsql
stable
security definer
set search_path=public
as $$
declare v_role public.team_roles%rowtype; v_actor_role uuid;
begin
    if p_actor is null or p_role is null then return false; end if;
    select * into v_role from public.team_roles where id=p_role and team_id=p_team;
    if not found then return false; end if;
    if public.is_team_owner(p_team,p_actor) then return true; end if;
    if not public.team_has_permission(p_team,p_actor,'manage_roles') then return false; end if;
    select role_id into v_actor_role from public.team_members where team_id=p_team and user_id=p_actor;
    if v_actor_role=p_role then return false; end if;
    -- Built-in Admin/Member definitions are owner-controlled. This is defense
    -- in depth on top of the strict permission hierarchy.
    if v_role.is_system then return false; end if;
    return public.devnest_permissions_strictly_dominate(
      public.devnest_effective_permissions(p_team,p_actor),v_role.permissions
    );
end;
$$;

create or replace function public.team_create_role(p_team_id uuid, p_name text, p_permissions jsonb)
returns uuid language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_role uuid; v_rank integer;
begin
    if not (public.is_team_owner(p_team_id,v_actor) or public.team_has_permission(p_team_id,v_actor,'manage_roles')) then
        raise exception 'not allowed';
    end if;
    if char_length(trim(p_name)) not between 1 and 80 then raise exception 'invalid role name'; end if;
    if not public.devnest_permissions_valid(p_permissions) then raise exception 'invalid role permissions'; end if;
    if not public.is_team_owner(p_team_id,v_actor)
       and not public.devnest_permissions_strictly_dominate(
         public.devnest_effective_permissions(p_team_id,v_actor),coalesce(p_permissions,'{}'::jsonb)
       ) then
        raise exception 'new role must be strictly below your effective permissions';
    end if;
    v_rank := public.devnest_permission_rank(coalesce(p_permissions,'{}'::jsonb));
    insert into public.team_roles(team_id,name,rank,permissions)
      values(p_team_id,trim(p_name),v_rank,coalesce(p_permissions,'{}'::jsonb))
      returning id into v_role;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_actor,'role_created','Role created',trim(p_name),
             jsonb_build_object('role_id',v_role,'derived_rank',v_rank));
    return v_role;
end;
$$;

create or replace function public.team_update_role(p_role_id uuid, p_name text, p_permissions jsonb)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_role public.team_roles%rowtype; v_new_rank int;
begin
    select * into v_role from public.team_roles where id=p_role_id for update;
    if not found then raise exception 'role not found'; end if;
    if not public.team_can_manage_role(v_role.team_id,v_actor,p_role_id) then
        raise exception 'cannot edit your own, a system, equal, or higher role';
    end if;
    if char_length(trim(p_name)) not between 1 and 80 then raise exception 'invalid role name'; end if;
    if not public.devnest_permissions_valid(p_permissions) then raise exception 'invalid role permissions'; end if;
    if not public.is_team_owner(v_role.team_id,v_actor)
       and not public.devnest_permissions_strictly_dominate(
         public.devnest_effective_permissions(v_role.team_id,v_actor),coalesce(p_permissions,'{}'::jsonb)
       ) then
        raise exception 'cannot promote a role to your own, equal, or higher permissions';
    end if;
    v_new_rank := public.devnest_permission_rank(coalesce(p_permissions,'{}'::jsonb));
    update public.team_roles
      set name=trim(p_name),rank=v_new_rank,permissions=coalesce(p_permissions,'{}'::jsonb),updated_at=now()
      where id=p_role_id;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(v_role.team_id,v_actor,'role_updated','Role updated',trim(p_name),
             jsonb_build_object('role_id',p_role_id,'derived_rank',v_new_rank));
    return true;
end;
$$;

create or replace function public.team_assign_role(p_team_id uuid, p_user_id uuid, p_role_id uuid)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid(); v_role public.team_roles%rowtype;
begin
    if not public.team_can_manage_member(p_team_id,v_actor,p_user_id) then
        raise exception 'cannot manage this member';
    end if;
    select * into v_role from public.team_roles where id=p_role_id and team_id=p_team_id;
    if not found then raise exception 'role not found'; end if;
    if not public.is_team_owner(p_team_id,v_actor) then
        if v_role.is_system and lower(v_role.name)='admin' then
            raise exception 'only the team owner can assign the system Admin role';
        end if;
        if not public.devnest_permissions_strictly_dominate(
          public.devnest_effective_permissions(p_team_id,v_actor),v_role.permissions
        ) then
            raise exception 'cannot assign an equal or higher role';
        end if;
    end if;
    update public.team_members set role_id=p_role_id where team_id=p_team_id and user_id=p_user_id;
    if not found then raise exception 'member not found'; end if;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_actor,'role_assigned','Role assigned','',jsonb_build_object('user_id',p_user_id,'role_id',p_role_id));
    return true;
end;
$$;

create or replace function public.team_set_member_permission(p_team_id uuid, p_user_id uuid, p_permission text, p_allow boolean)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_actor uuid:=auth.uid();
begin
    if p_permission not in ('view_project','edit_project','delete_project','create_note','edit_note','delete_note','create_decision','edit_decision','delete_decision','edit_architecture','manage_access','manage_roles','invite_members') then
       raise exception 'unknown permission';
    end if;
    if not public.team_can_manage_member(p_team_id,v_actor,p_user_id) then
       raise exception 'cannot manage this member';
    end if;
    if p_allow is null then
      delete from public.team_member_permission_overrides where team_id=p_team_id and user_id=p_user_id and permission_key=p_permission;
    else
      insert into public.team_member_permission_overrides(team_id,user_id,permission_key,allow,updated_at)
      values(p_team_id,p_user_id,p_permission,p_allow,now())
      on conflict(team_id,user_id,permission_key) do update set allow=excluded.allow,updated_at=now();
    end if;
    -- Re-evaluate *after* the proposed override. Raising rolls the statement
    -- back, so a manager cannot grant a target equal/superior effective rights.
    if not public.is_team_owner(p_team_id,v_actor)
       and not public.devnest_permissions_strictly_dominate(
         public.devnest_effective_permissions(p_team_id,v_actor),
         public.devnest_effective_permissions(p_team_id,p_user_id)
       ) then
       raise exception 'member permissions must remain strictly below your own';
    end if;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail,metadata)
      values(p_team_id,v_actor,'member_permission_changed','Member permission changed',p_permission,
             jsonb_build_object('user_id',p_user_id,'allow',p_allow));
    return true;
end;
$$;

-- Invitations always land in the built-in Member role. A custom low-score role
-- must never silently become the default just because its derived score is low.
create or replace function public.team_respond_invitation(p_invitation_id uuid, p_accept boolean)
returns boolean language plpgsql security definer set search_path=public
as $$
declare v_user uuid:=auth.uid(); v_inv public.team_invitations%rowtype; v_default_role uuid; v_team_name text;
begin
    select * into v_inv from public.team_invitations where id=p_invitation_id and invitee_id=v_user and status='pending' for update;
    if not found then raise exception 'pending invitation not found'; end if;
    if p_accept then
        select id into v_default_role from public.team_roles
          where team_id=v_inv.team_id and is_system and lower(name)='member'
          order by created_at asc limit 1;
        if v_default_role is null then
          select id into v_default_role from public.team_roles where team_id=v_inv.team_id order by rank asc,created_at asc limit 1;
        end if;
        insert into public.team_members(team_id,user_id,role_id) values(v_inv.team_id,v_user,v_default_role)
        on conflict(team_id,user_id) do update set role_id=coalesce(public.team_members.role_id,excluded.role_id);
        update public.team_invitations set status='accepted',responded_at=now() where id=p_invitation_id;
    else
        update public.team_invitations set status='declined',responded_at=now() where id=p_invitation_id;
    end if;
    select name into v_team_name from public.teams where id=v_inv.team_id;
    insert into public.user_notifications(user_id,event_type,title,detail,metadata)
      select owner_id,'team_invite_response','Team invitation response',
             coalesce((select username from public.profiles where id=v_user),'member') || case when p_accept then ' accepted ' else ' declined ' end || v_team_name,
             jsonb_build_object('team_id',v_inv.team_id,'user_id',v_user,'accepted',p_accept)
      from public.teams where id=v_inv.team_id;
    insert into public.team_activity(team_id,actor_id,event_type,title,detail)
      values(v_inv.team_id,v_user,case when p_accept then 'invite_accepted' else 'invite_declined' end,
             case when p_accept then 'Invitation accepted' else 'Invitation declined' end,'');
    return p_accept;
end;
$$;

-- Internal hierarchy helpers are not callable as public REST RPC endpoints.
revoke all on function public.devnest_effective_permissions(uuid,uuid) from public,anon,authenticated;
revoke all on function public.devnest_permissions_strictly_dominate(jsonb,jsonb) from public,anon,authenticated;
revoke all on function public.team_can_manage_role(uuid,uuid,uuid) from public,anon,authenticated;

-- Existing public RPC signatures keep their authenticated grants after CREATE
-- OR REPLACE, but re-grant explicitly so this migration is safe on fresh and
-- upgraded projects alike.
grant execute on function public.team_create_role(uuid,text,jsonb) to authenticated;
grant execute on function public.team_update_role(uuid,text,jsonb) to authenticated;
grant execute on function public.team_assign_role(uuid,uuid,uuid) to authenticated;
grant execute on function public.team_set_member_permission(uuid,uuid,text,boolean) to authenticated;
grant execute on function public.team_respond_invitation(uuid,boolean) to authenticated;

commit;
