def  dog_age(h_age):
 if h_age<0:
 	exit()
 elif h_age<=2:
	 d_age=10.5 * h_age
 else:
	 d_age = 21 + (h_age - 2)*4
 return  d_age
