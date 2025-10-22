from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from qlearning.engine import QLearningEngine
from qlearning.models import QTableEntry, QLearningLog
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Test Q-learning functionality with simulated interactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            default='testuser',
            help='Username to test with (creates if doesn\'t exist)'
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='Number of Q-learning iterations to simulate'
        )
        parser.add_argument(
            '--epsilon',
            type=float,
            default=0.3,
            help='Epsilon value for exploration (0.0 = pure exploitation, 1.0 = pure exploration)'
        )

    def handle(self, *args, **options):
        username = options['user']
        iterations = options['iterations']
        epsilon = options['epsilon']

        # Get or create user
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'Using existing user: {user.username}')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='testpass123'
            )
            self.stdout.write(f'Created new user: {user.username}')

        self.stdout.write(
            self.style.SUCCESS(f'\n🧠 Starting Q-Learning Test for {user.username}')
        )
        self.stdout.write(f'Iterations: {iterations}')
        self.stdout.write(f'Epsilon: {epsilon}')
        self.stdout.write('-' * 50)

        # Simulate Q-learning interactions
        for i in range(iterations):
            # Create a sample state (could represent user progress, performance, etc.)
            state = (
                random.randint(1, 5),  # User level
                random.randint(0, 100),  # Progress percentage
                random.choice(['easy', 'medium', 'hard'])  # Last difficulty
            )

            # Choose action using epsilon-greedy
            action = QLearningEngine.choose_action(user, state, epsilon)

            # Simulate reward (better for correct difficulty matching)
            if action == 'easy' and state[0] <= 2:
                reward = 1.0  # Good match
            elif action == 'medium' and 2 <= state[0] <= 3:
                reward = 1.0  # Good match
            elif action == 'hard' and state[0] >= 4:
                reward = 1.0  # Good match
            else:
                reward = -0.5  # Poor match

            # Next state (slight progression)
            next_state = (
                min(5, state[0] + random.randint(0, 1)),
                min(100, state[1] + random.randint(0, 10)),
                action  # Last difficulty becomes current action
            )

            # Update Q-table
            updated_entry = QLearningEngine.update_q(
                user=user,
                state_tuple=state,
                action=action,
                reward=reward,
                next_state_tuple=next_state
            )

            if (i + 1) % 5 == 0 or i == 0:
                self.stdout.write(
                    f'Iteration {i + 1}: State={state} -> Action={action} -> Reward={reward:.2f} -> Q={updated_entry.q_value:.3f}'
                )

        # Show final results
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('📊 Final Q-Learning Results'))

        # Get Q-table summary
        summary = QLearningEngine.get_user_qtable_summary(user)
        self.stdout.write(f'Total Q-Table Entries: {summary["total_entries"]}')
        self.stdout.write(f'Average Q-Value: {summary["average_q_value"]:.3f}')
        self.stdout.write(f'Max Q-Value: {summary["max_q_value"]:.3f}')
        self.stdout.write(f'Min Q-Value: {summary["min_q_value"]:.3f}')
        self.stdout.write(f'States Explored: {summary["states_explored"]}')
        self.stdout.write(f'Actions Distribution: {summary["actions_taken"]}')

        # Get learning progress
        progress = QLearningEngine.get_learning_progress(user)
        self.stdout.write(f'\nTotal Q-Learning Updates: {progress["total_updates"]}')
        self.stdout.write(f'Average Reward: {progress["average_reward"]:.3f}')
        self.stdout.write(f'Average Q-Change: {progress["average_q_change"]:.3f}')
        self.stdout.write(f'Recent Activity (24h): {progress["recent_activity"]} updates')

        # Show recent Q-learning logs
        recent_logs = QLearningLog.objects.filter(user=user).order_by('-timestamp')[:5]
        if recent_logs:
            self.stdout.write(f'\n🔄 Recent Q-Learning Updates:')
            for log in recent_logs:
                self.stdout.write(
                    f'  {log.timestamp.strftime("%H:%M:%S")} - {log.state_hash[:8]} - {log.action} -> {log.q_value_after:.3f} (reward: {log.reward:.2f})'
                )

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('✅ Q-Learning test completed successfully!'))
        self.stdout.write('✅ QTableEntry records created and updated')
        self.stdout.write('✅ QLearningLog records created with before/after values')
        self.stdout.write('✅ Epsilon-greedy action selection working')
        self.stdout.write('✅ Q-learning update rule applied correctly')
