"""Append reviewed Batch 001 candidates; never replace existing records."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import creator_db as db

items = json.loads((ROOT / 'exports/batch_001_candidates.json').read_text(encoding='utf-8'))
header, existing = db.load_rows()
assert header == db.FIELDNAMES
weights = ['direct_comparable_score', 'genre_fit_score', 'activity_score', 'size_score', 'multi_game_score', 'contact_score', 'personality_fit_score', 'indie_affinity_score']
tier1 = {'Papers, Please', "That's Not My Neighbor", 'Contraband Police', 'Not Tonight', 'Quarantine Zone'}
added = []
for item in items:
    row = {key: 'Unknown' for key in header}
    row.update(creator_name=item['name'], primary_platform='YouTube', youtube_channel_url=item['profile'], youtube_channel_id=item.get('id','Unknown'), youtube_subscribers=str(item.get('subs','Unknown')), relevant_games='; '.join(item['games']), direct_comparable_count=str(len(tier1.intersection(item['games']))), last_active_date=item['activity'], language='English', country='Unknown', content_style=item.get('style','Gameplay commentary / playthroughs'), business_email=item.get('email','Unknown'), contact_page=item.get('contact','Unknown'), other_social_url=item.get('social','Unknown'), twitch_channel_url=item.get('twitch','Unknown'), public_contact_method=('Public business email' if item.get('email') else 'Public community/contact page' if item.get('contact') else 'Public social profile' if item.get('social') else 'Unknown'), notes='Batch 001. '+item['notes'], date_discovered='2026-09-12', last_verified='2026-09-12', source_query=item['query'], status='candidate', outreach_status='', high_priority='No')
    for index, url in enumerate(item['evidence'][:3],1):
        row[f'evidence_url_{index}'] = url
    row.update(dict(zip(weights, map(str,item['scores']))))
    row = db.apply_normalized_fields(row)
    if db.find_match_index(existing,db.identity_keys(row)) is not None:
        continue
    row['creator_id'] = db.next_creator_id(existing)
    existing.append(row)
    added.append(row)
with db.CSV_PATH.open('a',newline='',encoding='utf-8') as stream:
    csv.DictWriter(stream,fieldnames=header).writerows(added)
print(f'Appended {len(added)} reviewed candidates; total {len(existing)}.')
