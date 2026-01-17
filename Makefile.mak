local/schema:
	mkdir -p $@
	cd $@
	curl -O https://docs.oasis-open.org/ubl/os-UBL-2.1/UBL-2.1.zip
	unzip UBL-2.1.zip
	curl -O https://docs.peppol.eu/poacc/billing/3.0/files/PEPPOL-EN16931-UBL.sch
	curl -O https://docs.peppol.eu/poacc/billing/3.0/files/CEN-EN16931-UBL.sch

web: env-run
	gunicorn -k eventlet -w 1 schema_tools.web:app
