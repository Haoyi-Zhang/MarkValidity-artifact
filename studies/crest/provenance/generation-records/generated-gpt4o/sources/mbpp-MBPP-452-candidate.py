def loss_amount(actual_cost, sale_amount):
	if sale_amount > actual_cost:
		return sale_amount - actual_cost
	return None
