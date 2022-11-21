import ssl
# All broker and mongo information must correspond to Celery Broker and REST API
# This is an example with no connections placed within this file. <variable_name> 
# Please use the single node cookiecutter and copy celery/code to make sure everything matches!
broker_url = 'amqp://<broker_user>:<broker_password>@<broker_host>:<broker_port>/<broker_vhost>'
broker_use_ssl = {
    'keyfile': '<path_to_key.pem>',
    'certfile': '<path_to_cert.pem>',
    'ca_certs': '<path_to_cacert.pem>',
    'cert_reqs': ssl.CERT_REQUIRED
}
worker_send_task_events = True
result_expires = None
accept_content = ['json']
result_backend = "mongodb://<mongo_host>:<mongo_port>/?ssl=true&tlsCAFile=<path_to_cacert.pem>&tlsCertificateKeyFile=<path_to_cert.pem>"
mongodb_backend_settings = {
    "database": "<application_short_name>",
    "taskmeta_collection": "tombstone"
}
#If you are pip installing the requirements.txt. It has the cybercomq repo. Example add task!
imports = ("<github repo queue - example (cybercomq)>",)

#The cybercomq install url would be included in the requirements.txt
