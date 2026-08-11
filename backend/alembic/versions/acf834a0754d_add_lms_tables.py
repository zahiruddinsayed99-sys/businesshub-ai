"""Add LMS tables

Revision ID: acf834a0754d
Revises: 18b33edaa0be
Create Date: 2026-08-11 10:09:11.630417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'acf834a0754d'
down_revision: Union[str, None] = '18b33edaa0be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('courses',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_courses_organization_id_organizations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_courses'))
    )
    op.create_table('course_enrollments',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('course_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='ENROLLED', nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_course_enrollments_course_id_courses'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_course_enrollments_organization_id_organizations'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_course_enrollments_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_course_enrollments'))
    )
    op.create_index('uq_course_enrollments_org_user_course_active', 'course_enrollments', ['organization_id', 'user_id', 'course_id'], unique=True, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_table('course_modules',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('course_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_course_modules_course_id_courses'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_course_modules_organization_id_organizations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_course_modules'))
    )
    op.create_index('ix_course_modules_course_sort', 'course_modules', ['course_id', 'sort_order'], unique=False)
    op.create_table('lessons',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('module_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content_body', sa.Text(), nullable=True),
    sa.Column('video_url', sa.String(length=512), nullable=True),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['module_id'], ['course_modules.id'], name=op.f('fk_lessons_module_id_course_modules'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_lessons_organization_id_organizations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lessons'))
    )
    op.create_index('ix_lessons_module_sort', 'lessons', ['module_id', 'sort_order'], unique=False)
    op.create_table('lesson_progress',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('enrollment_id', sa.UUID(), nullable=False),
    sa.Column('lesson_id', sa.UUID(), nullable=False),
    sa.Column('is_completed', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['enrollment_id'], ['course_enrollments.id'], name=op.f('fk_lesson_progress_enrollment_id_course_enrollments'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name=op.f('fk_lesson_progress_lesson_id_lessons'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_lesson_progress_organization_id_organizations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lesson_progress'))
    )
    op.create_table('quizzes',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('lesson_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name=op.f('fk_quizzes_lesson_id_lessons'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_quizzes_organization_id_organizations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quizzes'))
    )
    op.create_table('quiz_attempts',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('quiz_id', sa.UUID(), nullable=False),
    sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('passed', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_quiz_attempts_organization_id_organizations'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], name=op.f('fk_quiz_attempts_quiz_id_quizzes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_quiz_attempts_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quiz_attempts'))
    )
    op.create_table('quiz_questions',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('quiz_id', sa.UUID(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], name=op.f('fk_quiz_questions_quiz_id_quizzes'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quiz_questions'))
    )
    op.create_table('quiz_answers',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('answer_text', sa.String(length=512), nullable=False),
    sa.Column('is_correct', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], name=op.f('fk_quiz_answers_question_id_quiz_questions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quiz_answers'))
    )
    op.create_table('quiz_responses',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('attempt_id', sa.UUID(), nullable=False),
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('selected_answer_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['attempt_id'], ['quiz_attempts.id'], name=op.f('fk_quiz_responses_attempt_id_quiz_attempts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], name=op.f('fk_quiz_responses_question_id_quiz_questions'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['selected_answer_id'], ['quiz_answers.id'], name=op.f('fk_quiz_responses_selected_answer_id_quiz_answers'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quiz_responses'))
    )

def downgrade() -> None:
    op.drop_table('quiz_responses')
    op.drop_table('quiz_answers')
    op.drop_table('quiz_questions')
    op.drop_table('quiz_attempts')
    op.drop_table('quizzes')
    op.drop_table('lesson_progress')
    op.drop_index('ix_lessons_module_sort', table_name='lessons')
    op.drop_table('lessons')
    op.drop_index('ix_course_modules_course_sort', table_name='course_modules')
    op.drop_table('course_modules')
    op.drop_index('uq_course_enrollments_org_user_course_active', table_name='course_enrollments', postgresql_where=sa.text('deleted_at IS NULL'))
    op.drop_table('course_enrollments')
    op.drop_table('courses')
