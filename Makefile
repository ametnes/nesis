.PHONY: all

swagger:
	python nesis/api/spec/main.py --destination="docs/src/apps/swagger.yaml"
