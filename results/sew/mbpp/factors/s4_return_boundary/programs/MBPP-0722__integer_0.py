def  filter_data(students,h,w):
    result={k: s for  k, s in  students.items() if  h <=s[0] and  w <=s[1]}
    return  result    