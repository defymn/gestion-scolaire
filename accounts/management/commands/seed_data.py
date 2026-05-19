from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q

from accounts.college_demo import assign_college_demo_course_teachers
from accounts.models import ClassGroup, Parent, Student, Teacher, User
from courses.models import Attendance, Course, Grade, Schedule

# Anciens groupes / filières (seed non marocain) à supprimer à chaque run
LEGACY_CLASS_GROUP_NAMES = (
    'Class A',
    'Class B',
    'TC1 - Groupe A',
    'TC1 - Groupe B',
    '1BAC Sciences - Groupe 1',
    '1BAC Sciences - Groupe 2',
    '2BAC Physique-Chimie',
    '2BAC Sciences de la Vie et de la Terre',
    '1BAC SVT — Groupe A',  # remplacé par 1BAC EXP
)

# Anciens course_id du premier seed (CRS001, …)
LEGACY_COURSE_IDS = tuple(f'CRS{i:03}' for i in range(1, 50))

# Classes / groupes : TC (tronc commun), collège, 1BAC SM / EXP, 2BAC PC / SM / SVT
CLASS_GROUP_DEFS = [
    ('TC1 — Groupe A', 2026),
    ('TC1 — Groupe B', 2026),
    ('1AC — Groupe 1', 2026),
    ('1AC — Groupe 2', 2026),
    ('2AC — Groupe 1', 2026),
    ('2AC — Groupe 2', 2026),
    ('3AC — Groupe 1', 2026),
    ('3AC — Groupe 2', 2026),
    ('1BAC SM — Groupe A', 2026),
    ('1BAC SM — Groupe B', 2026),
    ('1BAC EXP — Groupe A', 2026),
    ('1BAC EXP — Groupe B', 2026),
    ('2BAC PC', 2026),
    ('2BAC SM — A', 2026),
    ('2BAC SM — B', 2026),
    ('2BAC SVT', 2026),
]

# course_id ≤ 20 car. (modèle) — (id, intitulé, crédits/heures تقريبية, classe/groupe, index prof)
COURSE_DEFS = [
    # Tronc commun 1ère année (TC1)
    ('MOR-T1A-AR', 'Langue arabe', 5, 'TC1 — Groupe A', 0),
    ('MOR-T1A-FR', 'Français', 5, 'TC1 — Groupe A', 1),
    ('MOR-T1A-MA', 'Mathématiques', 4, 'TC1 — Groupe A', 2),
    ('MOR-T1A-AS', 'Activité scientifique', 3, 'TC1 — Groupe A', 3),
    ('MOR-T1A-HG', 'Histoire-Géographie', 2, 'TC1 — Groupe A', 4),
    ('MOR-T1A-EI', 'Éducation islamique', 2, 'TC1 — Groupe A', 5),
    ('MOR-T1A-EP', 'Éducation physique et sportive', 2, 'TC1 — Groupe A', 4),
    ('MOR-T1A-IC', 'Instruction civique', 1, 'TC1 — Groupe A', 4),
    ('MOR-T1B-AR', 'Langue arabe', 5, 'TC1 — Groupe B', 0),
    ('MOR-T1B-FR', 'Français', 5, 'TC1 — Groupe B', 1),
    ('MOR-T1B-MA', 'Mathématiques', 4, 'TC1 — Groupe B', 2),
    ('MOR-T1B-EI', 'Éducation islamique', 2, 'TC1 — Groupe B', 5),
    ('MOR-T1B-EP', 'Éducation physique et sportive', 2, 'TC1 — Groupe B', 4),
    ('MOR-T1B-IC', 'Instruction civique', 1, 'TC1 — Groupe B', 4),
    # 1ère année collège
    ('MOR-1A1-AR', 'Langue arabe', 5, '1AC — Groupe 1', 0),
    ('MOR-1A1-FR', 'Français', 5, '1AC — Groupe 1', 1),
    ('MOR-1A1-MA', 'Mathématiques', 4, '1AC — Groupe 1', 2),
    ('MOR-1A1-AS', 'Activité scientifique', 3, '1AC — Groupe 1', 3),
    ('MOR-1A1-HG', 'Histoire-Géographie', 2, '1AC — Groupe 1', 4),
    ('MOR-1A1-EI', 'Éducation islamique', 2, '1AC — Groupe 1', 5),
    ('MOR-1A1-EP', 'Éducation physique et sportive', 2, '1AC — Groupe 1', 4),
    ('MOR-1A1-IC', 'Instruction civique', 1, '1AC — Groupe 1', 4),
    ('MOR-1A1-EA', 'Éducation artistique', 2, '1AC — Groupe 1', 5),
    ('MOR-1A2-AR', 'Langue arabe', 5, '1AC — Groupe 2', 0),
    ('MOR-1A2-FR', 'Français', 5, '1AC — Groupe 2', 1),
    ('MOR-1A2-MA', 'Mathématiques', 4, '1AC — Groupe 2', 2),
    ('MOR-1A2-AS', 'Activité scientifique', 3, '1AC — Groupe 2', 3),
    ('MOR-1A2-HG', 'Histoire-Géographie', 2, '1AC — Groupe 2', 4),
    ('MOR-1A2-EI', 'Éducation islamique', 2, '1AC — Groupe 2', 5),
    ('MOR-1A2-EP', 'Éducation physique et sportive', 2, '1AC — Groupe 2', 4),
    ('MOR-1A2-IC', 'Instruction civique', 1, '1AC — Groupe 2', 4),
    ('MOR-1A2-EA', 'Éducation artistique', 2, '1AC — Groupe 2', 5),
    # 2ème année collège
    ('MOR-2A1-AR', 'Langue arabe', 4, '2AC — Groupe 1', 0),
    ('MOR-2A1-FR', 'Français', 4, '2AC — Groupe 1', 1),
    ('MOR-2A1-AN', 'Anglais', 3, '2AC — Groupe 1', 1),
    ('MOR-2A1-MA', 'Mathématiques', 4, '2AC — Groupe 1', 2),
    ('MOR-2A1-PC', 'Physique-Chimie', 3, '2AC — Groupe 1', 3),
    ('MOR-2A1-HG', 'Histoire-Géographie', 2, '2AC — Groupe 1', 4),
    ('MOR-2A1-EI', 'Éducation islamique', 2, '2AC — Groupe 1', 5),
    ('MOR-2A1-EP', 'Éducation physique et sportive', 2, '2AC — Groupe 1', 4),
    ('MOR-2A1-IC', 'Instruction civique', 1, '2AC — Groupe 1', 4),
    ('MOR-2A2-AR', 'Langue arabe', 4, '2AC — Groupe 2', 0),
    ('MOR-2A2-FR', 'Français', 4, '2AC — Groupe 2', 1),
    ('MOR-2A2-MA', 'Mathématiques', 4, '2AC — Groupe 2', 2),
    ('MOR-2A2-PC', 'Physique-Chimie', 3, '2AC — Groupe 2', 3),
    ('MOR-2A2-HG', 'Histoire-Géographie', 2, '2AC — Groupe 2', 4),
    ('MOR-2A2-AN', 'Anglais', 3, '2AC — Groupe 2', 1),
    ('MOR-2A2-EI', 'Éducation islamique', 2, '2AC — Groupe 2', 5),
    ('MOR-2A2-EP', 'Éducation physique et sportive', 2, '2AC — Groupe 2', 4),
    ('MOR-2A2-IC', 'Instruction civique', 1, '2AC — Groupe 2', 4),
    # 3ème année collège (الإستعداد لولوج الجذع المشترك العلمي)
    ('MOR-3A1-AR', 'Langue arabe', 4, '3AC — Groupe 1', 0),
    ('MOR-3A1-FR', 'Français', 4, '3AC — Groupe 1', 1),
    ('MOR-3A1-AN', 'Anglais', 3, '3AC — Groupe 1', 1),
    ('MOR-3A1-MA', 'Mathématiques', 4, '3AC — Groupe 1', 2),
    ('MOR-3A1-PC', 'Physique-Chimie', 3, '3AC — Groupe 1', 3),
    ('MOR-3A1-SV', 'Sciences de la Vie et de la Terre', 3, '3AC — Groupe 1', 3),
    ('MOR-3A1-HG', 'Histoire-Géographie', 2, '3AC — Groupe 1', 4),
    ('MOR-3A1-EI', 'Éducation islamique', 2, '3AC — Groupe 1', 5),
    ('MOR-3A1-EP', 'Éducation physique et sportive', 2, '3AC — Groupe 1', 4),
    ('MOR-3A1-IC', 'Instruction civique', 1, '3AC — Groupe 1', 4),
    ('MOR-3A2-AR', 'Langue arabe', 4, '3AC — Groupe 2', 0),
    ('MOR-3A2-FR', 'Français', 4, '3AC — Groupe 2', 1),
    ('MOR-3A2-MA', 'Mathématiques', 4, '3AC — Groupe 2', 2),
    ('MOR-3A2-PC', 'Physique-Chimie', 3, '3AC — Groupe 2', 3),
    ('MOR-3A2-SV', 'Sciences de la Vie et de la Terre', 3, '3AC — Groupe 2', 3),
    ('MOR-3A2-HG', 'Histoire-Géographie', 2, '3AC — Groupe 2', 4),
    ('MOR-3A2-EI', 'Éducation islamique', 2, '3AC — Groupe 2', 5),
    ('MOR-3A2-AN', 'Anglais', 3, '3AC — Groupe 2', 1),
    ('MOR-3A2-EP', 'Éducation physique et sportive', 2, '3AC — Groupe 2', 4),
    ('MOR-3A2-IC', 'Instruction civique', 1, '3AC — Groupe 2', 4),
    # 1ère année bac — Sciences mathématiques
    ('MOR-1SMA-MA', 'Mathématiques', 7, '1BAC SM — Groupe A', 2),
    ('MOR-1SMA-PC', 'Physique-Chimie', 5, '1BAC SM — Groupe A', 3),
    ('MOR-1SMA-SV', 'Sciences de la Vie et de la Terre', 4, '1BAC SM — Groupe A', 3),
    ('MOR-1SMA-FR', 'Français', 3, '1BAC SM — Groupe A', 1),
    ('MOR-1SMA-AR', 'Langue arabe', 3, '1BAC SM — Groupe A', 0),
    ('MOR-1SMA-AN', 'Anglais', 3, '1BAC SM — Groupe A', 1),
    ('MOR-1SMA-PH', 'Philosophie', 2, '1BAC SM — Groupe A', 4),
    ('MOR-1SMA-EP', 'Éducation physique et sportive', 2, '1BAC SM — Groupe A', 4),
    ('MOR-1SMA-TIC', "Technologies de l'information", 2, '1BAC SM — Groupe A', 2),
    ('MOR-1SMB-MA', 'Mathématiques', 7, '1BAC SM — Groupe B', 2),
    ('MOR-1SMB-PC', 'Physique-Chimie', 5, '1BAC SM — Groupe B', 3),
    ('MOR-1SMB-FR', 'Français', 3, '1BAC SM — Groupe B', 1),
    ('MOR-1SMB-AN', 'Anglais', 3, '1BAC SM — Groupe B', 1),
    ('MOR-1SMB-EP', 'Éducation physique et sportive', 2, '1BAC SM — Groupe B', 4),
    # 1ère année bac — Sciences expérimentales (EXP)
    ('MOR-1EXA-MA', 'Mathématiques', 5, '1BAC EXP — Groupe A', 2),
    ('MOR-1EXA-PC', 'Physique-Chimie', 4, '1BAC EXP — Groupe A', 3),
    ('MOR-1EXA-SV', 'Sciences de la Vie et de la Terre', 5, '1BAC EXP — Groupe A', 3),
    ('MOR-1EXA-FR', 'Français', 3, '1BAC EXP — Groupe A', 1),
    ('MOR-1EXA-AR', 'Langue arabe', 3, '1BAC EXP — Groupe A', 0),
    ('MOR-1EXA-AN', 'Anglais', 3, '1BAC EXP — Groupe A', 1),
    ('MOR-1EXA-PH', 'Philosophie', 2, '1BAC EXP — Groupe A', 4),
    ('MOR-1EXA-EP', 'Éducation physique et sportive', 2, '1BAC EXP — Groupe A', 4),
    ('MOR-1EXA-AM', 'Langue amazighe', 2, '1BAC EXP — Groupe A', 0),
    ('MOR-1EXB-MA', 'Mathématiques', 5, '1BAC EXP — Groupe B', 2),
    ('MOR-1EXB-PC', 'Physique-Chimie', 4, '1BAC EXP — Groupe B', 3),
    ('MOR-1EXB-SV', 'Sciences de la Vie et de la Terre', 5, '1BAC EXP — Groupe B', 3),
    ('MOR-1EXB-FR', 'Français', 3, '1BAC EXP — Groupe B', 1),
    ('MOR-1EXB-EP', 'Éducation physique et sportive', 2, '1BAC EXP — Groupe B', 4),
    # 2ème année bac — Sciences physiques
    ('MOR-2PC-PHY', 'Physique approfondie', 6, '2BAC PC', 3),
    ('MOR-2PC-CHG', 'Chimie générale', 4, '2BAC PC', 3),
    ('MOR-2PC-CHO', 'Chimie organique', 4, '2BAC PC', 3),
    ('MOR-2PC-MAT', 'Mathématiques', 5, '2BAC PC', 2),
    ('MOR-2PC-FR', 'Français', 3, '2BAC PC', 1),
    ('MOR-2PC-PHI', 'Philosophie', 4, '2BAC PC', 4),
    ('MOR-2PC-EP', 'Éducation physique et sportive', 2, '2BAC PC', 4),
    ('MOR-2PC-AR', 'Langue arabe', 3, '2BAC PC', 0),
    # 2ème année bac — Sciences mathématiques
    ('MOR-2SMA-M1', 'Mathématiques I', 6, '2BAC SM — A', 2),
    ('MOR-2SMA-M2', 'Mathématiques II', 5, '2BAC SM — A', 2),
    ('MOR-2SMA-PH', 'Physique', 5, '2BAC SM — A', 3),
    ('MOR-2SMA-FR', 'Français', 3, '2BAC SM — A', 1),
    ('MOR-2SMA-PHI', 'Philosophie', 4, '2BAC SM — A', 4),
    ('MOR-2SMA-EP', 'Éducation physique et sportive', 2, '2BAC SM — A', 4),
    ('MOR-2SMA-AR', 'Langue arabe', 3, '2BAC SM — A', 0),
    ('MOR-2SMB-M1', 'Mathématiques I', 6, '2BAC SM — B', 2),
    ('MOR-2SMB-M2', 'Mathématiques II', 5, '2BAC SM — B', 2),
    ('MOR-2SMB-PH', 'Physique', 5, '2BAC SM — B', 3),
    ('MOR-2SMB-FR', 'Français', 3, '2BAC SM — B', 1),
    ('MOR-2SMB-PHI', 'Philosophie', 4, '2BAC SM — B', 4),
    ('MOR-2SMB-EP', 'Éducation physique et sportive', 2, '2BAC SM — B', 4),
    ('MOR-2SMB-AR', 'Langue arabe', 3, '2BAC SM — B', 0),
    # 2ème année bac — Sciences de la Vie et de la Terre
    ('MOR-2SV-MAT', 'Mathématiques', 4, '2BAC SVT', 2),
    ('MOR-2SV-SVT', 'SVT approfondies', 6, '2BAC SVT', 3),
    ('MOR-2SV-BIO', 'Biologie et géologie', 4, '2BAC SVT', 3),
    ('MOR-2SV-PC', 'Physique-Chimie', 3, '2BAC SVT', 3),
    ('MOR-2SV-FR', 'Français', 3, '2BAC SVT', 1),
    ('MOR-2SV-AR', 'Langue arabe', 3, '2BAC SVT', 0),
    ('MOR-2SV-PHI', 'Philosophie', 4, '2BAC SVT', 4),
    ('MOR-2SV-EP', 'Éducation physique et sportive', 2, '2BAC SVT', 4),
    ('MOR-2SV-AN', 'Anglais', 3, '2BAC SVT', 1),
]


class Command(BaseCommand):
    help = 'Seed initial sample data for School Management System.'

    def _purge_legacy_classgroups_and_courses(self):
        legacy_groups = ClassGroup.objects.filter(name__in=LEGACY_CLASS_GROUP_NAMES)
        legacy_ids = list(legacy_groups.values_list('pk', flat=True))
        course_filter = Q(course_id__in=LEGACY_COURSE_IDS) | Q(course_id__startswith='MOR-1SVA-')
        if legacy_ids:
            course_filter |= Q(class_group_id__in=legacy_ids)
        deleted_total, del_details = Course.objects.filter(course_filter).delete()
        _, grp_details = legacy_groups.delete()
        n_grp = grp_details.get('accounts.ClassGroup', 0)
        if deleted_total or n_grp:
            self.stdout.write(
                self.style.WARNING(
                    f'Nettoyage legacy: {n_grp} groupe(s) (Class A/B, TC1, anciennes filières bac). '
                    f'Objets supprimés au total (cours + enchaînements): {deleted_total}.'
                )
            )

    def _seed_student_portfolio(self, students):
        """Notes, présences et emploi du temps pour tous les cours de la classe de chaque élève (vues compte étudiant)."""
        days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        rooms = ['101', '102', 'Lab', 'Multimédia', 'EPS', 'Arts']

        def add_minutes(t, minutes):
            d = datetime.combine(date.min, t) + timedelta(minutes=minutes)
            return d.time()

        seen_group_ids = set()
        for student in students:
            gid = student.class_group_id
            if not gid:
                continue
            courses = list(Course.objects.filter(class_group_id=gid).order_by('course_id'))
            if not courses:
                continue

            if gid not in seen_group_ids:
                Schedule.objects.filter(course__class_group_id=gid).delete()
                for i, course in enumerate(courses):
                    day = days_order[i % 5]
                    period = (i // 5) % 6
                    sh = 8 + period
                    sm = (i * 11 + 5) % 50
                    st = time(sh, sm)
                    en = add_minutes(st, 55)
                    Schedule.objects.create(
                        course=course,
                        day=day,
                        start_time=st,
                        end_time=en,
                        room=f'Salle {rooms[i % len(rooms)]}',
                    )
                seen_group_ids.add(gid)

            for idx, course in enumerate(courses):
                base = 10 + (idx % 9) + (student.pk % 4) * 0.25
                Grade.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'value': round(min(base, 20), 2),
                        'grade_type': ('exam', 'quiz', 'homework')[idx % 3],
                        'comment': 'Données de démonstration',
                    },
                )
                for k in range(4):
                    ad = date.today() - timedelta(days=7 * k + idx + (student.pk % 5))
                    Attendance.objects.get_or_create(
                        student=student,
                        course=course,
                        date=ad,
                        defaults={'status': ('present', 'present', 'late', 'absent')[k % 4]},
                    )

    def handle(self, *args, **options):
        self._purge_legacy_classgroups_and_courses()

        admin_user, _ = User.objects.get_or_create(
            username='admin1',
            defaults={'role': 'admin', 'is_staff': True, 'is_superuser': True, 'first_name': 'System', 'last_name': 'Admin'},
        )
        admin_user.set_password('Admin123!')
        admin_user.save()

        groups = {}
        for name, year in CLASS_GROUP_DEFS:
            cg, _ = ClassGroup.objects.get_or_create(name=name, year=year)
            groups[name] = cg

        groupe_1ac = groups['1AC — Groupe 1']
        groupe_2ac = groups['2AC — Groupe 1']

        teachers = []
        for i in range(1, 7):
            user, _ = User.objects.get_or_create(
                username=f'teacher{i}',
                defaults={'role': 'teacher', 'first_name': f'Enseignant{i}', 'last_name': 'Prof'},
            )
            user.set_password('Teacher123!')
            user.save()
            teacher, _ = Teacher.objects.get_or_create(user=user, defaults={'teacher_id': f'TCH{i:03}'})
            teachers.append(teacher)

        students = []
        for i in range(1, 6):
            user, _ = User.objects.get_or_create(
                username=f'student{i}',
                defaults={'role': 'student', 'first_name': f'Élève{i}', 'last_name': 'User'},
            )
            user.set_password('Student123!')
            user.save()
            student, _ = Student.objects.get_or_create(
                user=user,
                defaults={
                    'student_id': f'STU{i:03}',
                    'date_of_birth': date(2010, (i % 12) + 1, (i % 28) + 1),
                    'class_group': groupe_1ac if i <= 3 else groupe_2ac,
                },
            )
            students.append(student)

        # Comptes élèves créés via signup sans classe : rattacher à 1AC — Groupe 1 pour affichage notes / EDT
        n_fixed = Student.objects.filter(class_group__isnull=True).update(class_group=groupe_1ac)
        if n_fixed:
            self.stdout.write(self.style.WARNING(f'{n_fixed} student profile(s) without class -> assigned to 1AC Groupe 1.'))

        for idx, student in enumerate(students, start=1):
            target = groupe_1ac if idx <= 3 else groupe_2ac
            if student.class_group_id != target.id:
                student.class_group = target
                student.save(update_fields=['class_group'])

        for i in range(1, 3):
            user, _ = User.objects.get_or_create(
                username=f'parent{i}',
                defaults={'role': 'parent', 'first_name': f'Parent{i}', 'last_name': 'User'},
            )
            user.set_password('Parent123!')
            user.save()
            parent, _ = Parent.objects.get_or_create(user=user)
            if i == 1:
                parent.children.set(students[:3])
            else:
                parent.children.set(students[3:])

        for course_id, title, credits, group_name, teacher_idx in COURSE_DEFS:
            Course.objects.get_or_create(
                course_id=course_id,
                defaults={
                    'name': title,
                    'credits': credits,
                    'teacher': teachers[teacher_idx % len(teachers)],
                    'class_group': groups[group_name],
                },
            )

        assign_college_demo_course_teachers(log=lambda msg: self.stdout.write(self.style.WARNING(msg)))

        self._seed_student_portfolio(Student.objects.filter(class_group__isnull=False))

        n_groups = ClassGroup.objects.count()
        n_courses = Course.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Sample data seeded: {n_groups} classes/groupes, {n_courses} cours (référentiel type Maroc).'))
