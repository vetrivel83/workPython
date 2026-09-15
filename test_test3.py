import importlib


def test_test3_can_be_imported():
	"""Test that the Test3 module loads without raising an exception."""
	module = importlib.import_module("Test3")

	assert module is not None


