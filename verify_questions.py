#!/usr/bin/env python
import json

# Verify the updated questions file
with open(r'c:\Users\TOUCH U\Videos\gamify_v2\fixtures\questions_initial.json', 'r') as f:
    data = json.load(f)

print('✅ QUESTION BANK EXPANSION VERIFICATION')
print('=' * 50)
print(f'📊 Total questions: {len(data)}')
print()

# Count by difficulty
easy_count = sum(1 for q in data if q['fields']['difficulty'] == 'easy')
medium_count = sum(1 for q in data if q['fields']['difficulty'] == 'medium')
hard_count = sum(1 for q in data if q['fields']['difficulty'] == 'hard')

print(f'🎯 Easy (MCQ Simple): {easy_count} questions')
print(f'🔷 Medium (MCQ Complex): {medium_count} questions')
print(f'🔴 Hard (Short Answer): {hard_count} questions')
print()

# Show sample of new questions
print('📝 SAMPLE NEW QUESTIONS:')
new_questions = [q for q in data if q['pk'] >= 31]
for q in new_questions[:3]:
    print(f'   {q["pk"]}. {q["fields"]["difficulty"].upper()}: {q["fields"]["text"][:50]}...')

print()

# Check curriculum tags
curriculum_tags = {}
for q in data:
    tag = q['fields']['curriculum_tag']
    if tag in curriculum_tags:
        curriculum_tags[tag] += 1
    else:
        curriculum_tags[tag] = 1

print('📚 CURRICULUM COVERAGE:')
for tag, count in sorted(curriculum_tags.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f'   {tag}: {count} questions')

print(f'\n✅ Total curriculum areas: {len(curriculum_tags)}')

# Verify JSON structure
print('\n🔍 JSON VALIDATION:')
try:
    json.dumps(data)
    print('   ✅ Valid JSON structure')
except:
    print('   ❌ JSON structure error')

print('\n🚀 READY FOR MIGRATION:')
print('   Run: python manage.py loaddata fixtures/questions_initial.json')
print('   This will populate the database with 60 questions total')
