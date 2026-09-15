try:
    
	number = float(input("Enter a number: "))
	print(f"The square of {number} is {number ** 2}")
    print(f"The cube of {number} is {number ** 3}")    
except ValueError:
	print("Please enter a valid number.")

