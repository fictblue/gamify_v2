import os
import sys
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamify_ai.settings')
django.setup()

from quizzes.models import Question

def load_questions():
    # Hapus semua pertanyaan yang ada
    Question.objects.all().delete()
    print("Menghapus semua pertanyaan yang ada...")
    
    # Muat pertanyaan easy
    with open('fixtures/questions_easy.json', 'r', encoding='utf-8') as f:
        easy_questions = json.load(f)
        for q in easy_questions:
            Question.objects.create(
                text=q['fields']['text'],
                difficulty=q['fields']['difficulty'],
                format=q['fields']['format'],
                options=q['fields']['options'],
                answer_key=q['fields']['answer_key'],
                curriculum_tag=q['fields']['curriculum_tag'],
                explanation=q['fields'].get('explanation', '')
            )
    print(f"Berhasil memuat {len(easy_questions)} soal easy")
    
    # Muat pertanyaan medium
    with open('fixtures/questions_medium.json', 'r', encoding='utf-8') as f:
        medium_questions = json.load(f)
        for q in medium_questions:
            Question.objects.create(
                text=q['fields']['text'],
                difficulty=q['fields']['difficulty'],
                format=q['fields']['format'],
                options=q['fields']['options'],
                answer_key=q['fields']['answer_key'],
                curriculum_tag=q['fields']['curriculum_tag'],
                explanation=q['fields'].get('explanation', '')
            )
    print(f"Berhasil memuat {len(medium_questions)} soal medium")
    
    # Muat pertanyaan hard
    with open('fixtures/questions_hard.json', 'r', encoding='utf-8') as f:
        hard_questions = json.load(f)
        for q in hard_questions:
            Question.objects.create(
                text=q['fields']['text'],
                difficulty=q['fields']['difficulty'],
                format=q['fields']['format'],
                options=q['fields'].get('options', {}),
                answer_key=q['fields']['answer_key'],
                curriculum_tag=q['fields']['curriculum_tag'],
                explanation=q['fields'].get('explanation', '')
            )
    print(f"Berhasil memuat {len(hard_questions)} soal hard")
    
    # Tampilkan total soal per tingkat kesulitan
    print("\nTotal soal yang berhasil dimuat:")
    print(f"- Easy: {Question.objects.filter(difficulty='easy').count()}")
    print(f"- Medium: {Question.objects.filter(difficulty='medium').count()}")
    print(f"- Hard: {Question.objects.filter(difficulty='hard').count()}")
    print(f"Total: {Question.objects.count()} soal")

if __name__ == "__main__":
    load_questions()
