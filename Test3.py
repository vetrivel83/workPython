"""Console application for calculating employee payroll."""


class Employee:
	def __init__(self, name: str, monthly_salary: float, bonus_percentage: float) -> None:
		self.name = name
		self.monthly_salary = monthly_salary
		self.bonus_percentage = bonus_percentage
		self.validate_inputs()

	def validate_inputs(self) -> None:
		if not isinstance(self.name, str) or not self.name.strip():
			raise ValueError("Name must not be empty.")
		if self.monthly_salary < 0:
			raise ValueError("Monthly salary cannot be negative.")
		if not 0 <= self.bonus_percentage <= 100:
			raise ValueError("Bonus percentage must be between 0 and 100.")
	def annual_salary(self) -> float:
		return self.monthly_salary * 12

	def bonus(self) -> float:
		return self.annual_salary() * self.bonus_percentage / 100

	def total_compensation(self) -> float:
		return self.annual_salary() + self.bonus()

	def summary(self) -> str:
		return (
			f"{self.name:<25} {self.annual_salary():>15,.2f} "
			f"{self.bonus():>12,.2f} {self.total_compensation():>18,.2f}"
	)


def read_float(prompt: str, minimum: float = 0, maximum: float | None = None) -> float:
	while True:
		try:
			value = float(input(prompt))
			if value < minimum or (maximum is not None and value > maximum):
				raise ValueError
			return value
		except ValueError:
			limit = f" and at most {maximum}" if maximum is not None else ""
			print(f"Enter a valid number from {minimum}{limit}.")

def main() -> None:
	employees: list[Employee] = []
	print("Employee Payroll System")
	while True:
		name = input("Employee name (press Enter to finish): ").strip()
		if not name:
			break
		salary = read_float("Monthly salary: ")
		percentage = read_float("Bonus percentage (0-100): ", 0, 100)
		employees.append(Employee(name, salary, percentage))
		print("Employee added.\n")

	if not employees:
		print("No employees entered.")
		return

	print("\nPayroll Summary")
	print("-" * 78)
	print(f"{'Employee':<25} {'Annual Salary':>15} {'Bonus':>12} {'Total Compensation':>18}")
	print("-" * 78)
	for employee in employees:
		print(employee.summary())
	print("-" * 78)


if __name__ == "__main__":
	main()
