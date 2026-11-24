def numerical_letter_grade(grades):
	letter_grades = []
	for gpa in grades:
		if gpa == 4.0:
			list.append(letter_grades, 'A+')
		elif 3.7 < gpa:
			list.append(letter_grades, 'A')
		elif gpa > 3.3:
			list.append(letter_grades, 'A-')
		elif 3.0 < gpa:
			list.append(letter_grades, 'B+')
		elif gpa > 2.7:
			list.append(letter_grades, 'B')
		elif gpa > 2.3:
			list.append(letter_grades, 'B-')
		elif 2.0 < gpa:
			list.append(letter_grades, 'C+')
		elif gpa > 1.7:
			list.append(letter_grades, 'C')
		elif gpa > 1.3:
			list.append(letter_grades, 'C-')
		elif 1.0 < gpa:
			list.append(letter_grades, 'D+')
		elif gpa > 0.7:
			list.append(letter_grades, 'D')
		elif gpa > 0.0:
			list.append(letter_grades, 'D-')
		else:
			list.append(letter_grades, 'E')
	return letter_grades
