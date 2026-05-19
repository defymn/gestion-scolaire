"""
Assignation des cours démo collège (1AC — Groupe 1, 2AC — Groupe 1) aux enseignants.

Tous les comptes prof hors seed (teacher1–teacher6) partagent ces cours par paires
(une matière 1AC + une 2AC) pour que chacun voie les deux classes et les élèves démo.
Sans aucun tel prof, tout est assigné à teacher1.
"""
from __future__ import annotations

from itertools import zip_longest

DEMO_1AC = '1AC — Groupe 1'
DEMO_2AC = '2AC — Groupe 1'
SEED_TEACHER_USERNAMES = {f'teacher{i}' for i in range(1, 7)}


def assign_college_demo_course_teachers(log=None):
    """
    log: optional callable(str) e.g. command.stdout.write
    """
    from accounts.models import ClassGroup, Teacher, User
    from courses.models import Course

    g1 = ClassGroup.objects.filter(name=DEMO_1AC).order_by('-year').first()
    g2 = ClassGroup.objects.filter(name=DEMO_2AC).order_by('-year').first()
    if not g1 or not g2:
        if log:
            log('College demo: class groups 1AC/2AC G1 missing, skip course assignment.')
        return

    c1 = list(Course.objects.filter(class_group=g1).order_by('course_id'))
    c2 = list(Course.objects.filter(class_group=g2).order_by('course_id'))
    if not c1 and not c2:
        return

    pairs = list(zip_longest(c1, c2))
    recipients = list(Teacher.objects.exclude(user__username__in=SEED_TEACHER_USERNAMES).order_by('id'))

    to_update = []
    if not recipients:
        user = User.objects.filter(username='teacher1', role='teacher').first()
        if not user or not hasattr(user, 'teacher_profile'):
            if log:
                log('College demo: no custom teachers and no teacher1, skip.')
            return
        t = user.teacher_profile
        for a, b in pairs:
            if a is not None:
                a.teacher = t
                to_update.append(a)
            if b is not None:
                b.teacher = t
                to_update.append(b)
        if log:
            log('College demo: all 1AC/2AC G1 courses assigned to @teacher1.')
    else:
        for ti, (a, b) in enumerate(pairs):
            t = recipients[ti % len(recipients)]
            if a is not None:
                a.teacher = t
                to_update.append(a)
            if b is not None:
                b.teacher = t
                to_update.append(b)
        if log:
            names = ', '.join(f'@{r.user.username}' for r in recipients)
            log(f'College demo: 1AC/2AC G1 courses split across {len(recipients)} prof(s): {names}.')

    if to_update:
        Course.objects.bulk_update(to_update, ['teacher'], batch_size=200)
