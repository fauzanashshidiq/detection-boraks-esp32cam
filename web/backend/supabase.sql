create table if not exists detections (
  id uuid primary key default gen_random_uuid(),
  label text not null,
  confidence numeric not null,
  probabilities jsonb,
  image_url text,
  source text,
  created_at timestamptz default now()
);

create index if not exists detections_created_at_idx
on detections (created_at desc);
