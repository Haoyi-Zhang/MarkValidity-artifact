def subject_marks(subjectmarks):
#subject_marks = [('English', 88), ('Science', 90), ('Maths', 97), ('Social sciences', 82)])
	return sorted(subjectmarks, key=lambda x: x[1])
