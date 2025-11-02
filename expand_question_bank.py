#!/usr/bin/env python
"""
Generate additional questions for GamifyLearn question bank expansion
Current: 30 questions (10 per difficulty)
Target: 60 questions (20 per difficulty)
"""

import json

def generate_additional_questions():
    """Generate 10 additional questions for each difficulty level"""

    # EASY QUESTIONS (MCQ Simple) - Additional 10 questions (pk 31-40)
    easy_questions = [
        {
            "model": "quizzes.question",
            "pk": 31,
            "fields": {
                "text": "Choose the correct form: I _____ to the store yesterday.",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "go",
                    "B": "went",
                    "C": "goes",
                    "D": "going"
                },
                "answer_key": "B",
                "curriculum_tag": "Grammar - Past Simple",
                "explanation": "We use 'went' (past simple) for actions completed in the past.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 32,
            "fields": {
                "text": "What is the plural of 'mouse' (animal)?",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "mouses",
                    "B": "mice",
                    "C": "mouse",
                    "D": "mices"
                },
                "answer_key": "B",
                "curriculum_tag": "Vocabulary - Irregular Plurals",
                "explanation": "'Mice' is the correct irregular plural form of 'mouse'.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 33,
            "fields": {
                "text": "Complete: She _____ her homework every evening.",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "do",
                    "B": "does",
                    "C": "did",
                    "D": "doing"
                },
                "answer_key": "B",
                "curriculum_tag": "Grammar - Present Simple Third Person",
                "explanation": "For third person singular (she), we add 'es' to the verb in present simple.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 34,
            "fields": {
                "text": "Choose the correct word: I have _____ apples in my bag.",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "much",
                    "B": "many",
                    "C": "a lot",
                    "D": "some"
                },
                "answer_key": "D",
                "curriculum_tag": "Grammar - Countable Nouns",
                "explanation": "We use 'some' with countable nouns in positive sentences.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 35,
            "fields": {
                "text": "What time _____ you usually wake up?",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "do",
                    "B": "does",
                    "C": "are",
                    "D": "is"
                },
                "answer_key": "A",
                "curriculum_tag": "Grammar - Question Formation",
                "explanation": "In questions with 'you', we use the auxiliary verb 'do'.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 36,
            "fields": {
                "text": "Choose the correct adjective: This is a _____ day today.",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "beauty",
                    "B": "beautiful",
                    "C": "beautify",
                    "D": "beauties"
                },
                "answer_key": "B",
                "curriculum_tag": "Grammar - Adjectives",
                "explanation": "'Beautiful' is the correct adjective form to describe the noun 'day'.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 37,
            "fields": {
                "text": "Complete the question: _____ book is this? It's mine.",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "Who",
                    "B": "Whose",
                    "C": "What",
                    "D": "Which"
                },
                "answer_key": "B",
                "curriculum_tag": "Grammar - Possessive Questions",
                "explanation": "'Whose' is used to ask about ownership or possession.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 38,
            "fields": {
                "text": "Choose the correct adverb: She sings _____.",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "beautiful",
                    "B": "beauty",
                    "C": "beautifully",
                    "D": "beauties"
                },
                "answer_key": "C",
                "curriculum_tag": "Grammar - Adverbs",
                "explanation": "'Beautifully' is the adverb form that describes how she sings.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 39,
            "fields": {
                "text": "What is the past tense of 'run'?",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "run",
                    "B": "ran",
                    "C": "running",
                    "D": "runs"
                },
                "answer_key": "B",
                "curriculum_tag": "Grammar - Irregular Verbs",
                "explanation": "'Ran' is the correct past tense form of the irregular verb 'run'.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 40,
            "fields": {
                "text": "Choose the correct subject pronoun: _____ am a student.",
                "difficulty": "easy",
                "format": "mcq_simple",
                "options": {
                    "A": "He",
                    "B": "She",
                    "C": "I",
                    "D": "They"
                },
                "answer_key": "C",
                "curriculum_tag": "Grammar - Subject Pronouns",
                "explanation": "'I' is the correct first person singular subject pronoun.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        }
    ]

    # MEDIUM QUESTIONS (MCQ Complex) - Additional 10 questions (pk 41-50)
    medium_questions = [
        {
            "model": "quizzes.question",
            "pk": 41,
            "fields": {
                "text": "Which of the following are irregular verbs? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "Go",
                    "B": "Walk",
                    "C": "Eat",
                    "D": "Swim",
                    "E": "Run"
                },
                "answer_key": "[\"A\", \"C\", \"D\"]",
                "curriculum_tag": "Grammar - Irregular Verbs",
                "explanation": "Go (went), eat (ate), and swim (swam) are irregular verbs. Walk and run are regular verbs.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 42,
            "fields": {
                "text": "Which of the following can function as both nouns and verbs? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "Book",
                    "B": "Run",
                    "C": "Water",
                    "D": "Jump",
                    "E": "Table"
                },
                "answer_key": "[\"A\", \"B\", \"C\", \"D\"]",
                "curriculum_tag": "Grammar - Word Classes",
                "explanation": "Book, run, water, and jump can function as both nouns and verbs. Table is typically only a noun.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 43,
            "fields": {
                "text": "Which of the following are linking verbs? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "Be",
                    "B": "Seem",
                    "C": "Appear",
                    "D": "Run",
                    "E": "Look"
                },
                "answer_key": "[\"A\", \"B\", \"C\", \"E\"]",
                "curriculum_tag": "Grammar - Linking Verbs",
                "explanation": "Be, seem, appear, and look are linking verbs that connect subjects to adjectives. Run is an action verb.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 44,
            "fields": {
                "text": "Which of the following are determiners? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "The",
                    "B": "This",
                    "C": "Some",
                    "D": "Quickly",
                    "E": "Many"
                },
                "answer_key": "[\"A\", \"B\", \"C\", \"E\"]",
                "curriculum_tag": "Grammar - Determiners",
                "explanation": "The, this, some, and many are determiners. Quickly is an adverb.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 45,
            "fields": {
                "text": "Which of the following are phrasal verbs? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "Look up",
                    "B": "Give up",
                    "C": "Take off",
                    "D": "Beautiful",
                    "E": "Turn on"
                },
                "answer_key": "[\"A\", \"B\", \"C\", \"E\"]",
                "curriculum_tag": "Vocabulary - Phrasal Verbs",
                "explanation": "Look up, give up, take off, and turn on are phrasal verbs. Beautiful is an adjective.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 46,
            "fields": {
                "text": "Which of the following are conditional structures? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "Zero conditional",
                    "B": "First conditional",
                    "C": "Second conditional",
                    "D": "Present simple",
                    "E": "Third conditional"
                },
                "answer_key": "[\"A\", \"B\", \"C\", \"E\"]",
                "curriculum_tag": "Grammar - Conditional Sentences",
                "explanation": "Zero, first, second, and third conditional are conditional structures. Present simple is a tense.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 47,
            "fields": {
                "text": "Which of the following are passive voice structures? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "Subject + verb + object",
                    "B": "Subject + be + past participle",
                    "C": "Object + verb + subject",
                    "D": "Be + subject + past participle",
                    "E": "Subject + verb + complement"
                },
                "answer_key": "[\"B\", \"D\"]",
                "curriculum_tag": "Grammar - Passive Voice",
                "explanation": "Passive voice structures use 'be' + past participle with the subject.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 48,
            "fields": {
                "text": "Which of the following are relative clauses? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "Who",
                    "B": "Which",
                    "C": "That",
                    "D": "What",
                    "E": "Where"
                },
                "answer_key": "[\"A\", \"B\", \"C\", \"E\"]",
                "curriculum_tag": "Grammar - Relative Clauses",
                "explanation": "Who, which, that, and where are relative pronouns used in relative clauses. What is an interrogative pronoun.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 49,
            "fields": {
                "text": "Which of the following are reported speech changes? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "Present to past",
                    "B": "Past to past perfect",
                    "C": "Will to would",
                    "D": "This to that",
                    "E": "Here to there"
                },
                "answer_key": "[\"A\", \"B\", \"C\", \"D\", \"E\"]",
                "curriculum_tag": "Grammar - Reported Speech",
                "explanation": "All of these are common changes when converting direct speech to reported speech.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 50,
            "fields": {
                "text": "Which of the following are infinitive structures? (Select all that apply)",
                "difficulty": "medium",
                "format": "mcq_complex",
                "options": {
                    "A": "To play",
                    "B": "Playing",
                    "C": "To be played",
                    "D": "Played",
                    "E": "To have played"
                },
                "answer_key": "[\"A\", \"C\", \"E\"]",
                "curriculum_tag": "Grammar - Infinitives",
                "explanation": "To play, to be played, and to have played are infinitive structures. Playing and played are gerund and past participle forms.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        }
    ]

    # HARD QUESTIONS (Short Answer) - Additional 10 questions (pk 51-60)
    hard_questions = [
        {
            "model": "quizzes.question",
            "pk": 51,
            "fields": {
                "text": "Complete the sentence: The politician made a _____ to address the concerns of the people.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "commitment",
                "curriculum_tag": "Vocabulary - Political Terms",
                "explanation": "'Commitment' refers to a pledge or promise made by a politician to address specific issues or concerns.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 52,
            "fields": {
                "text": "Fill in the blank: The _____ of the ecosystem depends on biodiversity.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "stability",
                "curriculum_tag": "Vocabulary - Environmental Science",
                "explanation": "'Stability' refers to the balance and resilience of an ecosystem, which is maintained through biodiversity.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 53,
            "fields": {
                "text": "Complete the sentence: The _____ of the new technology has revolutionized communication.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "advent",
                "curriculum_tag": "Vocabulary - Technology",
                "explanation": "'Advent' refers to the arrival or introduction of something significant, especially new technology.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 54,
            "fields": {
                "text": "Fill in the blank: The artist's _____ style made his paintings instantly recognizable.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "signature",
                "curriculum_tag": "Vocabulary - Art and Design",
                "explanation": "'Signature' refers to a distinctive style or characteristic that makes something easily identifiable.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 55,
            "fields": {
                "text": "Complete the sentence: The _____ between the two theories has been debated for years.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "discrepancy",
                "curriculum_tag": "Vocabulary - Academic Discourse",
                "explanation": "'Discrepancy' refers to a difference or inconsistency between two theories or sets of facts.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 56,
            "fields": {
                "text": "Fill in the blank: The _____ of the research findings has significant implications for policy.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "magnitude",
                "curriculum_tag": "Vocabulary - Research and Statistics",
                "explanation": "'Magnitude' refers to the size, extent, or importance of research findings and their impact.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 57,
            "fields": {
                "text": "Complete the sentence: The _____ of the ancient manuscript revealed secrets of the past.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "decipherment",
                "curriculum_tag": "Vocabulary - Historical Research",
                "explanation": "'Decipherment' refers to the process of decoding or interpreting ancient manuscripts or texts.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 58,
            "fields": {
                "text": "Fill in the blank: The _____ of the economic crisis affected millions of people worldwide.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "repercussions",
                "curriculum_tag": "Vocabulary - Economics",
                "explanation": "'Repercussions' refers to the consequences or effects of an economic crisis that spread widely.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 59,
            "fields": {
                "text": "Complete the sentence: The _____ of the peace treaty brought hope to the region.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "ratification",
                "curriculum_tag": "Vocabulary - International Law",
                "explanation": "'Ratification' refers to the formal approval or confirmation of a peace treaty by official bodies.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        },
        {
            "model": "quizzes.question",
            "pk": 60,
            "fields": {
                "text": "Fill in the blank: The _____ of the new curriculum requires comprehensive teacher training.",
                "difficulty": "hard",
                "format": "short_answer",
                "options": None,
                "answer_key": "implementation",
                "curriculum_tag": "Vocabulary - Education Policy",
                "explanation": "'Implementation' refers to the process of putting a new curriculum into practice, requiring proper training and resources.",
                "created_at": "2025-09-26T10:00:00Z",
                "updated_at": "2025-09-26T10:00:00Z"
            }
        }
    ]

    return easy_questions, medium_questions, hard_questions

def update_fixtures_file():
    """Update the questions_initial.json file with new questions"""

    # Read current file
    with open(r'c:\Users\TOUCH U\Videos\gamify_v2\fixtures\questions_initial.json', 'r') as f:
        current_data = json.load(f)

    # Generate new questions
    easy_questions, medium_questions, hard_questions = generate_additional_questions()

    # Add new questions to current data
    updated_data = current_data + easy_questions + medium_questions + hard_questions

    # Write updated file
    with open(r'c:\Users\TOUCH U\Videos\gamify_v2\fixtures\questions_initial.json', 'w') as f:
        json.dump(updated_data, f, indent=2)

    return len(easy_questions), len(medium_questions), len(hard_questions)

if __name__ == '__main__':
    print("🔧 EXPANDING QUESTION BANK")
    print("=" * 50)
    print("Current: 30 questions (10 per difficulty)")
    print("Target: 60 questions (20 per difficulty)")
    print()

    easy_count, medium_count, hard_count = update_fixtures_file()

    print("✅ ADDED QUESTIONS:")
    print(f"   Easy: +{easy_count} MCQ Simple (pk 31-40)")
    print(f"   Medium: +{medium_count} MCQ Complex (pk 41-50)")
    print(f"   Hard: +{hard_count} Short Answer (pk 51-60)")
    print()
    print("📊 NEW TOTALS:")
    print("   Easy: 20 questions (10 basic grammar + 10 extended grammar)")
    print("   Medium: 20 questions (10 basic concepts + 10 advanced concepts)")
    print("   Hard: 20 questions (10 basic vocabulary + 10 advanced vocabulary)")
    print()
    print("🎯 CURRICULUM COVERAGE:")
    print("   ✅ SMP Class VIII English standards")
    print("   ✅ Progressive difficulty scaling")
    print("   ✅ Comprehensive grammar and vocabulary")
    print("   ✅ Academic, scientific, and professional contexts")
    print()
    print("🚀 READY FOR MIGRATION:")
    print("   Run: python manage.py loaddata fixtures/questions_initial.json")
